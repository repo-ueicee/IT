library(tidyverse)

# 1. Cargar los datos
df <- read_csv("reporte_pip_2025.csv")

# 2. Filtrar solo Gestión Privada y asegurar el orden correcto de los niveles
df_privada <- df %>% 
  filter(str_detect(dependencia_funcional, "(?i)privada")) %>% 
  mutate(nivel = factor(nivel, levels = c("Nivel 0 (Previo)", "Nivel 1", "Nivel 2", "Nivel 3", "Nivel 4")))

# Definir las materias a evaluar
materias <- c("Matemática", "Lengua")

# Crear o abrir el archivo de texto donde se guardará todo el contenido para Claude
archivo_salida <- "datos_para_informes_claude.txt"
sink(archivo_salida)

# Obtener la lista de todos los jardines privados únicos
jardines <- unique(df_privada$establecimiento)

# Bucle principal: Recorrer cada jardín de infantes
for (jardin in jardines) {
  
  cat("======================================================================\n")
  cat("ESTABLECIMIENTO: ", expedited_jardin <- jardin, "\n")
  cat("======================================================================\n\n")
  
  # --- SECCIÓN 1: RESUMEN GENERAL DEL JARDÍN (Ambas materias) ---
  cat("## 1. RESUMEN GENERAL DEL JARDÍN\n\n")
  
  for (materia in materias) {
    df_jardin_materia <- df_privada %>% 
      filter(establecimiento == jardin, tab_nombre == materia)
    
    if (nrow(df_jardin_materia) > 0) {
      # Calcular Matrícula Total del Jardín para esta materia
      # (Máximo de alumnos acumulados en cualquiera de las preguntas)
      matricula_jardin <- df_jardin_materia %>% 
        group_by(select_preg) %>% 
        summarise(total_preg = sum(cant_alumnos, na.rm = TRUE)) %>% 
        pull(total_preg) %>% max()
      
      # Distribución General por Niveles en el Jardín
      resumen_jardin <- df_jardin_materia %>% 
        group_by(nivel) %>% 
        summarise(Alumnos = sum(cant_alumnos, na.rm = TRUE), .groups = 'drop') %>% 
        mutate(Porcentaje = (Alumnos / sum(Alumnos)) * 100)
      
      cat("### Materia: ", materia, "\n")
      cat("Matrícula Total Evaluada en el Jardín: ", matricula_jardin, " alumnos\n")
      cat("Distribución General por Niveles:\n")
      
      # Imprimir tabla limpia formato Markdown
      cat("| Nivel | Cantidad de Alumnos | Porcentaje |\n")
      cat("| :--- | :---: | :---: |\n")
      for(i in 1:nrow(resumen_jardin)) {
        cat(sprintf("| %s | %d | %.1f%% |\n", 
                    resumen_jardin$nivel[i], resumen_jardin$Alumnos[i], resumen_jardin$Porcentaje[i]))
      }
      cat("\n")
    }
  }
  
  # --- SECCIÓN 2: INFORMACIÓN DESAGREGADA POR SALITA ---
  cat("## 2. DESGLOSE POR SALITA (SECCIÓN)\n\n")
  
  # Obtener las salitas de este jardín específico
  salitas <- df_privada %>% 
    filter(establecimiento == jardin) %>% 
    distinct(id_seccion, nombre_seccion)
  
  for (s in 1:nrow(salitas)) {
    id_salita <- salitas$id_seccion[s]
    nom_salita <- salitas$nombre_seccion[s]
    
    cat("----------------------------------------------------------------------\n")
    cat("SALITA: ", nom_salita, " (ID: ", id_salita, ")\n")
    cat("----------------------------------------------------------------------\n\n")
    
    for (materia in materias) {
      df_salita_materia <- df_privada %>% 
        filter(id_seccion == id_salita, tab_nombre == materia)
      
      if (nrow(df_salita_materia) > 0) {
        # 1. Matrícula de la Salita
        matricula_salita <- df_salita_materia %>% 
          group_by(select_preg) %>% 
          summarise(total_preg = sum(cant_alumnos, na.rm = TRUE)) %>% 
          pull(total_preg) %>% max()
        
        # 2. Resumen de la Salita (Estilo Tarjeta)
        resumen_salita <- df_salita_materia %>% 
          group_by(nivel) %>% 
          summarise(Alumnos = sum(cant_alumnos, na.rm = TRUE), .groups = 'drop') %>% 
          mutate(Porcentaje = (Alumnos / sum(Alumnos)) * 100)
        
        cat("#### >> Área: ", materia, " (Matrícula en salita: ", matricula_salita, ")\n")
        cat("Resumen consolidado de la salita:\n")
        cat("| Nivel | Alumnos | Porcentaje |\n")
        cat("| :--- | :---: | :---: |\n")
        for(i in 1:nrow(resumen_salita)) {
          cat(sprintf("| %s | %d | %.1f%% |\n", 
                      resumen_salita$nivel[i], resumen_salita$Alumnos[i], resumen_salita$Porcentaje[i]))
        }
        cat("\n")
        
        # 3. Detalle por Pregunta / Dimensión (Estilo Tabla de Frecuencias)
        cat("Detalle por Dimensión Evaluada:\n")
        preguntas <- unique(df_salita_materia$select_preg)
        
        for (preg in preguntas) {
          df_preg <- df_salita_materia %>% filter(select_preg == preg)
          total_preg <- sum(df_preg$cant_alumnos)
          
          cat("* Dimensión: ", preg, " (Total respuestas: ", total_preg, ")\n")
          cat("  | Nivel | Alumnos | Porcentaje |\n")
          cat("  | :--- | :---: | :---: |\n")
          
          # Asegurar que muestre todos los niveles aunque tengan 0 alumnos
          niveles_completos <- tibble(nivel = factor(c("Nivel 0 (Previo)", "Nivel 1", "Nivel 2", "Nivel 3", "Nivel 4"))) %>% 
            left_join(df_preg, by = "nivel") %>% 
            mutate(cant_alumnos = replace_na(cant_alumnos, 0),
                   pct = (cant_alumnos / total_preg) * 100)
          
          for(i in 1:nrow(niveles_completos)) {
            cat(sprintf("  | %s | %d | %.1f%% |\n", 
                        niveles_completos$nivel[i], niveles_completos$cant_alumnos[i], niveles_completos$pct[i]))
          }
          cat("\n")
        }
      }
    }
  }
  cat("\n\n")
}

# Cerrar el archivo de texto
sink()
message("¡Listo! El archivo 'datos_para_informes_claude.txt' fue generado con éxito.")