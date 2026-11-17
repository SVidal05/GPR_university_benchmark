# GPR University Benchmark

## Descripción del proyecto

**GPR University Benchmark** es un proyecto de ciencia de datos cuyo objetivo es analizar y comparar universidades tecnológicas europeas mediante indicadores de internacionalización, recursos académicos, financiación y actividad investigadora.

El proyecto busca identificar diferencias y similitudes entre instituciones, estudiando cómo distribuyen sus recursos y desarrollan sus actividades académicas e investigadoras, sin establecer rankings de calidad universitaria.

Como **Producto Mínimo Viable (MVP)**, el análisis se centrará inicialmente en la **Universitat Politècnica de València (UPV)**, utilizando datos abiertos institucionales. Posteriormente, se pretende ampliar el estudio a otras universidades europeas, como Politecnico di Milano, TU Delft, KTH y EPFL.

## Exploración de no desempleo

El notebook `notebooks/DataXplorNoDesempleo.ipynb` contiene la exploración ejecutada
de los seis CSV de `data/raw/NoDesempleo`: calidad, descriptivos, evolución,
distribuciones, comparaciones por centro y titulación, panel común y cobertura.
Puede ejecutarse desde la raíz o desde `notebooks/` en un entorno Jupyter con
las dependencias de `requirements.txt` e IPython.

Para regenerar los CSV sin ejecutar Jupyter, desde la raíz:

```bash
python scripts/build_no_desempleo.py
streamlit run app.py
```

El proceso exporta en `data/processed/`:

- `upv_no_desempleo.csv`: detalle con archivo de origen.
- `upv_no_desempleo_anual.csv`: descriptivos por curso.
- `upv_no_desempleo_fuentes.csv`: inventario de archivos y codificaciones.
- `upv_titulaciones_integrado.csv`: unión externa con la tabla existente de
  movilidad y matrícula, validada por curso, RUCT, titulación y centro. Completa
  matrícula desde `upv_matricula.csv` cuando existe correspondencia exacta.
- `cobertura_no_desempleo.csv`: disponibilidad sobre las claves de esa unión.

La sección **No desempleo** del dashboard ofrece filtros, evolución, distribución,
medias por centro y descarga. **Calidad de datos** muestra su cobertura. Las tablas
previas se conservan. Los datos actuales incluyen 593 porcentajes y 897 filas en
la unión, de 2019-20 a 2024-25. Las otras 304 filas no tienen este indicador.
En 2019-20 el universo integrado solo contiene las claves de no desempleo.

Sin tamaños de muestra, las medias son simples entre titulaciones-centro y no
tasas globales de personas. No desempleo no equivale necesariamente a empleo.
Se conservan ceros y valores de 100%; no se imputan ausentes ni se pondera por
matrícula. La población encuestada y el momento de medición requieren consultar
la metodología de la fuente antes de interpretar estos valores como inserción laboral.

## Objetivos

### Objetivo general

Desarrollar un sistema de *benchmarking* basado en datos abiertos que permita caracterizar y comparar universidades tecnológicas europeas mediante indicadores académicos, económicos, de investigación e internacionalización.

### Objetivos específicos

- **Recopilar e integrar datos** procedentes de portales de transparencia, fuentes abiertas e informes institucionales.
- **Limpiar y homogeneizar la información** para garantizar la consistencia y comparabilidad de los datos.
- **Construir indicadores normalizados** que permitan analizar universidades de diferentes tamaños.
- **Analizar la evolución temporal** de los principales indicadores y estudiar las relaciones entre variables.
- **Aplicar técnicas de ciencia de datos**, como análisis de componentes principales (PCA) y clustering, para identificar perfiles institucionales.
- **Desarrollar visualizaciones interactivas** que faciliten la interpretación y comparación de resultados.
