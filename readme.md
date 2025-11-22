# Proyecto Nuam 

## Integrantes:
- Fernando Orellana
- Cristian Lorca
- Cesar Silva
- Javier Mendez



## Requerimientos Funcionales

-Que el sistema posea un mantenedor de calificaciones tributarias. Es importante para el proyecto porque esto permitirá mantener y mostrar el CRUD de las calificaciones.

-Que el sistema despliegue las calificaciones tributarias para su visibilidad general. Este requerimiento es muy importante para poder visualizar las calificaciones que ya están almacenadas en la base de datos.

-Que el sistema tenga un buscador personal de calificaciones con filtros. Es importante ya que nos ayuda a tener una búsqueda mucho más rápida a la hora de buscar una calificación.

-Que el sistema tenga una función para crear, eliminar y modificar calificaciones. Es necesario ya que nos ayuda a poder corregir o actualizar los datos evitando problemas.

-Que el sistema permita ingresar calificaciones (Por archivos de manera automática). Es importante ya que ahorra tiempo al cargar muchos datos de una sola vez, evitando hacerlo todo manual.

-Que el sistema permita el ingreso de calificaciones manualmente. Sirve en caso de que la cantidad de datos no sea tan grande o si es que no hay archivos con grandes cantidades de datos listos para ingresar.

-Que el sistema permita el ingreso de montos manualmente. Es útil cuando solo haya que ingresar cantidades bajas de valores, así evitamos cargar un archivo completo.

-Que el sistema permita la carga de archivos calificaciones masivas (monto-Dj1948).
	Nos ayuda a subir grandes cantidades de información, así esto se hace de manera mucho más fácil y eficiente, permitiendo leer archivos con el formato dj1948.

-Que el sistema permita la carga de archivos calificaciones masivas (factores).	Nos ayuda a manejar datos en grandes volúmenes de calificaciones.

-Que se dé a escoger cargar archivos o ingreso manualmente.	Es importante ya que le da una flexibilidad al usuario, así puede elegir la opción que más le acomode.

-Que se permita la carga de archivos en general. Formatos de archivos (CSV, Excel)

-Manejar instrumentos no inscritos permitiendo su gestión e identificación única. Esto no ayuda a trabajar con instrumentos no inscritos de forma ordenada, incluso si no están formalmente registrado.

-El sistema debe tener un control de acceso para que solo puedan entrar los corredores registrados.	Nos ayuda a tener un mayor control de la seguridad ya que solo las personas autorizadas tendrán acceso al sistema.

-Quiero que los datos se almacenen en una BD y que se puedan consultar en todo momento.	Es muy importante ya que aseguramos que la información quede guardada y que se pueda revisar en cualquier instante.



## Requerimientos No Funcionales

-El sistema debe estar optimizado y ser rápido. Es importante ya que el usuario así tiene una mejor experiencia utilizando el sistema a la hora de esperar consultas o hacer operaciones.

-Debe tener una interfaz intuitiva y fácil de usar. Es importante ya que ayudamos a que el usuario pueda tener una mejor experiencia y no necesite algún tipo de capacitación para utilizar el sistema.

-Se deben controlar los posibles errores. Es importante ya que procuramos tener un control para los errores y tener soluciones a la brevedad o de forma inmediata, para que el usuario pueda seguir trabajando.

-Se debe dar Feedback inmediato al usuario según su acción. Esto nos ayuda a que el usuario sepa si lo que hizo funciono realmente.

-El sistema debe estar disponible al menos al 99,99% del tiempo anual.    Esto nos ayuda a que el sistema siempre esté funcionando y el usuario no tenga que detener lo que está haciendo y así tampoco pierda archivos o datos.

-El sistema debe tener baja latencia al tratar con datos. Esto nos ayuda a tener una respuesta mucho más inmediata.

-El sistema debe ser escalable tanto en almacenamiento como en funcionalidades. Es importante ya que nos da la facilidad de que, si el sistema llega a crecer, podamos hacerlo sin la necesidad de rehacerlo desde cero.

-Se deben proteger los datos encriptándolos en su almacenamiento y transmisión. Es importante encriptar los datos para que si alguien llega a interceptar los datos le sea más difícil leer estos datos, así protegemos la información de los usuarios.

-Se deben registrar cambios en los datos para encontrar cambios no autorizados. Esto nos ayuda a tener registro de quien realizo los cambios en el sistema y así dar una mayor confianza de este.




## Flujo De La APP

Flujo Monstrado en el canva poner atencion al nombre de la diapositiva que indica la seccion a la que pertenece

https://www.canva.com/design/DAG11ImogyU/RMtgxG_9xear5kjS-MJOLA/edit?utm_content=DAG11ImogyU&utm_campaign=designshare&utm_medium=link2&utm_source=sharebutton



## Designacion de Tareas


-Fernando Orellana = Crear Los Models.py para importarlos a Supabase, Templates (Incio Sesion, Registro y otros Templates).

-Javier Mendez = Templates (Agregar Calificacion Tributaria y otros Templates).

-Cesar Silva =  Archivo exel "Plantilla" (Crear el archivo exel con los atributos para calificaciones tributarias masivas, y estudiar para la app tome los datos y rellene automaticamente).

-Cristian Lorca = Templates (NavBar "Barra de navegacion", Templates  Agregar Empresa y  otros Templates). 

Cada form que van a hacer depende de mirar como esta construida la base de datos






## Pasos para correr Proyecto Durante las Pruebas

1-Crear ambiente VENV

python -m venv venv

2-Entrar al entorno virtual con el archivo activate

activate.bat  para terminarles cmd y activate para shells

3-Intalar dependencias

pip install -r requirements.txt 

4-Descargar las variables de entorno del DS "4F env-nuam" para poder conectarse a la base de datos "por buenas practicas no se puede dejar en el repositorio" recuerda colocar el .env en el mismo nivel que el readme.md


5-Para cambiar "actualizar un modelo en la base de datos recuerden aplicar las migraciones"

python manage.py makemigrations Contenedor_Calificaciones

python manage.py migrate

6- Ejecutar proyecto para pruebas 

python manage.py runserver

7- Cree super usuario temporal para las pruebas

python manage.py createsuperuser

admin
admin

### Colores Usados
* #f5732c
* #afafaf

### Atributos de Calificaciones Tributarias
- calificacion_id (PK, dato fantasma)
- cuenta_id (FK), dato fantasma
- rut_empresa (FK) 👍🏻
- nombre_empresa (STR) 👍🏻
- anio_tributario (INT) 👍🏻
- tipo_calificacion (STR) 👍🏻
- monto_tributario (INT) 👍🏻
- factor_tributario (FLOAT) 👍🏻
- unidad_valor (CLP, UF, UTM, COP, UVT, Etc) 👍🏻
- puntaje_calificacion (De 0 a 100) 👍🏻
- categoria_calificacion (Bajo. Medio, Alto) 👍🏻
- nivel_riesgo (Bajo, Medio, Alto, Critico) 👍🏻
- metodo_calificacion (Masiva o Manual, dato fantasma) 
- modelo_version (STR) --- ELIMINADO ---
- fecha_calculo (Fecha y Hora actual, dato fantasma) 
- vigencia_desde (Fecha) --- ELIMINADO ---
- vigencia_hasta (Fecha) --- ELIMINADO ---
- fuente_calculo (Manaul o Masiva) --- ELIMINADO ---
- justificacion_resultado (STR) 👍🏻
- detalles (STR) ???? Archivos opcionales? --- ELIMINADO ---
- estado_calificacion (STR o Boolean, dato fantasma)

### Cosas pendientes
- Redireccion a tus empresas registradas (Filtro para mostrar empresas de una sola cuenta)
- Cambio en el navbar segun rol, falta jefe equipo.