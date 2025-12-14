# 📱 API REST - App Móvil del Jefe de Equipo

## 📋 Descripción General

API simplificada para la aplicación móvil del **Jefe de Equipo**. Permite gestionar calificaciones tributarias pendientes, revisar historial, ver equipo y administrar perfil.

---

## 🔐 Autenticación

### 1. Login (Solo Jefe de Equipo)

**Endpoint:** `POST /api/login/`

**Descripción:** Autenticación exclusiva para Jefes de Equipo.

**Request Body:**
```json
{
  "rut": "12345678-9",
  "contrasena": "tu_contraseña"
}
```

**Response (200 OK):**
```json
{
  "success": true,
  "message": "Bienvenido",
  "user": {
    "cuenta_id": 1,
    "nombre": "Juan",
    "apellido": "Pérez",
    "correo": "juan.perez@example.com",
    "telefono": "+56912345678",
    "equipo_id": 5,
    "equipo_nombre": "Equipo Alpha"
  }
}
```

**Response (401 Unauthorized):**
```json
{
  "success": false,
  "message": "Credenciales inválidas o acceso no autorizado",
  "errors": {...}
}
```

**Nota:** Si no eres Jefe de Equipo, recibirás error 401.

---

## 📊 Dashboard Principal

### 2. Dashboard con Estadísticas

**Endpoint:** `GET /api/dashboard/?equipo_id=1`

**Descripción:** Estadísticas completas para la pantalla de inicio.

**Query Params:**
- `equipo_id` (required): ID del equipo

**Response (200 OK):**
```json
{
  "total_pendientes_aprobar": 15,
  "total_aprobadas_hoy": 3,
  "total_rechazadas_hoy": 1,
  "total_pendientes_mes": 45,
  "total_aprobadas_mes": 28,
  "total_rechazadas_mes": 7,
  "total_calificaciones_equipo": 320,
  "promedio_puntaje_aprobadas": 72.5,
  "porcentaje_aprobacion": 80.0,
  "calificaciones_alto_riesgo": 5,
  "calificaciones_antiguas": 2,
  "top_calificador_nombre": "María González",
  "top_calificador_aprobadas": 45
}
```

**Datos Mostrados:**
- ✅ **Total pendientes por aprobar**: Calificaciones esperando revisión
- 📅 **Aprobadas/Rechazadas hoy**: Actividad del día
- 📈 **Estadísticas del mes**: Métricas mensuales
- 🎯 **Promedio de puntaje**: Calidad de las calificaciones aprobadas
- 📊 **Porcentaje de aprobación**: Tasa de éxito del equipo
- ⚠️ **Alertas**: Calificaciones de alto riesgo y antiguas sin revisar
- 🏆 **Top calificador**: Miembro más productivo

---

## 📋 Calificaciones Pendientes

### 3. Lista de Calificaciones por Aprobar

**Endpoint:** `GET /api/calificaciones-pendientes/?equipo_id=1`

**Descripción:** Todas las calificaciones pendientes de aprobación del equipo.

**Query Params:**
- `equipo_id` (required): ID del equipo

**Response (200 OK):**
```json
{
  "total": 15,
  "calificaciones": [
    {
      "calificacion_id": 123,
      "empresa_rut": "76123456-7",
      "empresa_nombre": "Tech Solutions SpA",
      "empresa_pais": "Chile",
      "anio_tributario": 2024,
      "tipo_calificacion": "Anual",
      "monto_tributario": 50000000,
      "factor_tributario": "Ingresos",
      "unidad_valor": "CLP",
      "puntaje_calificacion": 85,
      "categoria_calificacion": "A",
      "nivel_riesgo": "Bajo",
      "justificacion_resultado": "Empresa con buenos indicadores financieros...",
      "fecha_calculo": "2024-12-10T14:30:00Z",
      "calificador_nombre": "Carlos Soto"
    }
  ]
}
```

---

### 4. Detalle de Calificación

**Endpoint:** `GET /api/calificacion/{calificacion_id}/`

**Descripción:** Ver todos los detalles de una calificación específica.

**Response (200 OK):**
```json
{
  "calificacion_id": 123,
  "empresa_rut": "76123456-7",
  "empresa_nombre": "Tech Solutions SpA",
  "empresa_pais": "Chile",
  "anio_tributario": 2024,
  "tipo_calificacion": "Anual",
  "monto_tributario": 50000000,
  "factor_tributario": "Ingresos",
  "unidad_valor": "CLP",
  "puntaje_calificacion": 85,
  "categoria_calificacion": "A",
  "nivel_riesgo": "Bajo",
  "justificacion_resultado": "Análisis detallado de la empresa...",
  "fecha_calculo": "2024-12-10T14:30:00Z",
  "calificador_nombre": "Carlos Soto"
}
```

---

## ✅ Aprobar Calificación

### 5. Aprobar una Calificación

**Endpoint:** `POST /api/aprobar-calificacion/`

**Descripción:** Aprobar una calificación pendiente.

**Request Body:**
```json
{
  "calificacion_id": 123,
  "jefe_rut": "12345678-9",
  "observaciones": "Calificación correcta, se aprueba."
}
```

**Response (200 OK):**
```json
{
  "success": true,
  "message": "Calificación aprobada exitosamente"
}
```

**Response (400 Bad Request):**
```json
{
  "success": false,
  "errors": {
    "calificacion_id": ["Esta calificación ya no está pendiente de aprobación."]
  }
}
```

---

## ❌ Rechazar Calificación

### 6. Rechazar una Calificación

**Endpoint:** `POST /api/rechazar-calificacion/`

**Descripción:** Rechazar una calificación con observaciones.

**Request Body:**
```json
{
  "calificacion_id": 123,
  "jefe_rut": "12345678-9",
  "observaciones": "Los datos financieros no coinciden con los documentos adjuntos."
}
```

**Response (200 OK):**
```json
{
  "success": true,
  "message": "Calificación rechazada exitosamente"
}
```

---

## 📜 Historial de Calificaciones

### 7. Ver Historial (Aprobadas y Rechazadas)

**Endpoint:** `GET /api/historial/?equipo_id=1&estado=all`

**Descripción:** Historial completo de calificaciones revisadas.

**Query Params:**
- `equipo_id` (required): ID del equipo
- `estado` (optional): `all`, `aprobado`, `rechazado` (default: `all`)

**Response (200 OK):**
```json
{
  "total": 85,
  "historial": [
    {
      "calificacion_id": 120,
      "empresa_rut": "76123456-7",
      "empresa_nombre": "Tech Solutions SpA",
      "empresa_pais": "Chile",
      "anio_tributario": 2024,
      "puntaje_calificacion": 85,
      "categoria_calificacion": "A",
      "nivel_riesgo": "Bajo",
      "estado": "aprobado",
      "fecha_revision": "2024-12-13T10:00:00Z",
      "observaciones": "Aprobado correctamente",
      "calificador_nombre": "Carlos Soto"
    },
    {
      "calificacion_id": 119,
      "empresa_rut": "77654321-5",
      "empresa_nombre": "Servicios Financieros Ltda",
      "empresa_pais": "Chile",
      "anio_tributario": 2024,
      "puntaje_calificacion": 45,
      "categoria_calificacion": "C",
      "nivel_riesgo": "Alto",
      "estado": "rechazado",
      "fecha_revision": "2024-12-12T16:30:00Z",
      "observaciones": "Revisar cálculo del factor tributario",
      "calificador_nombre": "María González"
    }
  ]
}
```

**Uso en la App:**
- Filtrar por `estado=aprobado` para ver solo aprobadas
- Filtrar por `estado=rechazado` para ver solo rechazadas
- Usar `estado=all` para ver ambas

---

## 👥 Mi Equipo

### 8. Ver Miembros del Equipo

**Endpoint:** `GET /api/mi-equipo/?rut_jefe=12345678-9`

**Descripción:** Lista de calificadores del equipo con sus estadísticas.

**Query Params:**
- `rut_jefe` (required): RUT del jefe

**Response (200 OK):**
```json
{
  "equipo_nombre": "Equipo Alpha",
  "total_miembros": 5,
  "miembros": [
    {
      "rut": "98765432-1",
      "nombre_completo": "Carlos Soto Ramírez",
      "correo": "carlos.soto@example.com",
      "telefono": "+56912345678",
      "total_calificaciones": 120,
      "calificaciones_aprobadas": 95,
      "calificaciones_rechazadas": 20,
      "calificaciones_pendientes": 5
    },
    {
      "rut": "87654321-0",
      "nombre_completo": "María González López",
      "correo": "maria.gonzalez@example.com",
      "telefono": "+56987654321",
      "total_calificaciones": 150,
      "calificaciones_aprobadas": 130,
      "calificaciones_rechazadas": 15,
      "calificaciones_pendientes": 5
    }
  ]
}
```

---

## 👤 Perfil del Jefe

### 9. Ver Perfil

**Endpoint:** `GET /api/perfil/?rut=12345678-9`

**Descripción:** Obtener datos del perfil del jefe.

**Query Params:**
- `rut` (required): RUT del jefe

**Response (200 OK):**
```json
{
  "cuenta_id": 1,
  "rut": "12345678-9",
  "nombre": "Juan",
  "apellido": "Pérez",
  "correo": "juan.perez@example.com",
  "telefono": "+56912345678",
  "direccion": "Av. Principal 123, Santiago",
  "edad": 35,
  "equipo_nombre": "Equipo Alpha"
}
```

---

### 10. Actualizar Perfil

**Endpoint:** `PUT /api/perfil/`

**Descripción:** Actualizar datos del perfil (teléfono, correo, dirección).

**Request Body:**
```json
{
  "rut": "12345678-9",
  "telefono": "+56999888777",
  "correo": "nuevo.correo@example.com",
  "direccion": "Nueva Dirección 456"
}
```

**Response (200 OK):**
```json
{
  "success": true,
  "message": "Perfil actualizado correctamente",
  "data": {
    "cuenta_id": 1,
    "rut": "12345678-9",
    "nombre": "Juan",
    "apellido": "Pérez",
    "correo": "nuevo.correo@example.com",
    "telefono": "+56999888777",
    "direccion": "Nueva Dirección 456",
    "edad": 35,
    "equipo_nombre": "Equipo Alpha"
  }
}
```

---

## 🗺️ Navegación de la App

### Estructura de Navegación

```
┌─────────────────────────────────┐
│         NAVBAR INFERIOR          │
├─────────────────────────────────┤
│  [Inicio] [Historial] [Equipo]  │
│          [Perfil]                │
└─────────────────────────────────┘
```

### Pantallas Principales

1. **🏠 INICIO (Pendientes)**
   - Endpoint: `/api/dashboard/` + `/api/calificaciones-pendientes/`
   - Dashboard con estadísticas
   - Lista de calificaciones por aprobar
   - Botones: Ver detalle → Aprobar/Rechazar

2. **📜 HISTORIAL**
   - Endpoint: `/api/historial/?estado=all`
   - Tabs: Aprobadas | Rechazadas | Todas
   - Ver observaciones de cada calificación

3. **👥 EQUIPO**
   - Endpoint: `/api/mi-equipo/`
   - Lista de miembros
   - Estadísticas individuales

4. **👤 PERFIL**
   - Endpoint: `/api/perfil/`
   - Ver/editar datos personales
   - Botón: Cerrar sesión

---

## 🔄 Flujo de Trabajo

### 1. Login
```
Usuario ingresa RUT y contraseña
→ POST /api/login/
→ Guardar datos de sesión (cuenta_id, equipo_id, rut)
→ Navegar a pantalla Inicio
```

### 2. Dashboard (Pantalla Inicio)
```
Al entrar a la app
→ GET /api/dashboard/?equipo_id={equipo_id}
→ Mostrar tarjetas con estadísticas
→ GET /api/calificaciones-pendientes/?equipo_id={equipo_id}
→ Mostrar lista de pendientes
```

### 3. Aprobar/Rechazar Calificación
```
Usuario toca calificación en lista
→ GET /api/calificacion/{id}/
→ Mostrar detalles completos
→ Usuario decide: [Aprobar] o [Rechazar]
→ POST /api/aprobar-calificacion/ o POST /api/rechazar-calificacion/
→ Actualizar lista
```

### 4. Ver Historial
```
Usuario va a pantalla Historial
→ GET /api/historial/?equipo_id={equipo_id}&estado=all
→ Mostrar lista con filtros (tabs)
```

### 5. Ver Equipo
```
Usuario va a pantalla Equipo
→ GET /api/mi-equipo/?rut_jefe={rut}
→ Mostrar lista de miembros con estadísticas
```

### 6. Cerrar Sesión
```
Usuario toca "Cerrar Sesión" en Perfil
→ Limpiar datos de sesión local
→ Volver a pantalla de Login
```

---

## 📊 Datos Importantes del Dashboard

### Métricas Clave a Mostrar

1. **Tarjeta: Pendientes por Aprobar** ⏳
   - `total_pendientes_aprobar`
   - Color: Naranja/Amarillo
   - Acción: Toca para ver lista

2. **Tarjeta: Actividad de Hoy** 📅
   - `total_aprobadas_hoy` ✅
   - `total_rechazadas_hoy` ❌
   - Color: Verde/Rojo

3. **Tarjeta: Mes Actual** 📈
   - `total_aprobadas_mes`
   - `total_rechazadas_mes`
   - `total_pendientes_mes`
   - Gráfico de barras o circular

4. **Tarjeta: Alertas** ⚠️
   - `calificaciones_alto_riesgo` (prioridad alta)
   - `calificaciones_antiguas` (más de 7 días)
   - Color: Rojo

5. **Tarjeta: Rendimiento** 🎯
   - `promedio_puntaje_aprobadas`
   - `porcentaje_aprobacion`
   - Indicador visual (gauge/barra)

6. **Tarjeta: Top Calificador** 🏆
   - `top_calificador_nombre`
   - `top_calificador_aprobadas`
   - Ícono de trofeo

---

## 🎨 Sugerencias de UI

### Colores Sugeridos
- **Pendiente**: 🟡 Amarillo/Naranja
- **Aprobado**: 🟢 Verde
- **Rechazado**: 🔴 Rojo
- **Alto Riesgo**: 🔴 Rojo oscuro
- **Bajo Riesgo**: 🟢 Verde claro
- **Medio Riesgo**: 🟡 Amarillo

### Iconos Sugeridos
- Inicio: 🏠 (home)
- Historial: 📜 (history/list)
- Equipo: 👥 (people/group)
- Perfil: 👤 (person)
- Aprobar: ✅ (checkmark)
- Rechazar: ❌ (close/x)
- Alertas: ⚠️ (warning)

---

## 🔧 Configuración de Desarrollo

### Base URL
```
LOCAL: http://localhost:8000
PRODUCCIÓN: https://tu-dominio.com
```

### Headers Requeridos
```
Content-Type: application/json
Accept: application/json
```

### Manejo de Sesión
La app debe guardar localmente:
- `cuenta_id`
- `rut`
- `equipo_id`
- `nombre_completo`

Para enviar en cada request donde se requiera.

---

## ❗ Manejo de Errores

### Errores Comunes

**400 Bad Request**
```json
{
  "success": false,
  "errors": {
    "campo": ["Mensaje de error"]
  }
}
```

**401 Unauthorized**
```json
{
  "success": false,
  "message": "Credenciales inválidas o acceso no autorizado"
}
```

**404 Not Found**
```json
{
  "error": "Recurso no encontrado"
}
```

**500 Internal Server Error**
```json
{
  "success": false,
  "error": "Error interno del servidor"
}
```

---

## 🚀 Testing de Endpoints

### Usando curl

**Login:**
```bash
curl -X POST http://localhost:8000/api/login/ \
  -H "Content-Type: application/json" \
  -d '{"rut":"12345678-9","contrasena":"tu_password"}'
```

**Dashboard:**
```bash
curl -X GET "http://localhost:8000/api/dashboard/?equipo_id=1"
```

**Aprobar Calificación:**
```bash
curl -X POST http://localhost:8000/api/aprobar-calificacion/ \
  -H "Content-Type: application/json" \
  -d '{"calificacion_id":123,"jefe_rut":"12345678-9","observaciones":"Aprobado"}'
```

---

## 📝 Notas Importantes

1. ⚠️ **Seguridad**: Actualmente `permission_classes = []` para desarrollo. En producción, implementar autenticación JWT o token-based.

2. 🔒 **Contraseñas**: Actualmente se comparan en texto plano. En producción, usar Django password hashing.

3. 📱 **Paginación**: No implementada aún. Si hay muchas calificaciones, considerar añadir paginación.

4. 🔄 **Refresh**: La app debe refrescar datos después de aprobar/rechazar para actualizar contadores.

5. ✅ **Validaciones**: El backend valida que:
   - Solo Jefes de Equipo puedan loguearse
   - Solo se puedan aprobar/rechazar calificaciones en estado `por_aprobar`
   - El jefe pertenezca a un equipo válido

---

## 📞 Contacto y Soporte

Para dudas sobre la API, revisa este documento o consulta con el equipo de desarrollo backend.

---

**Versión:** 1.0  
**Fecha:** Diciembre 2024  
**Autor:** Equipo de Desarrollo Proyecto Nuam
