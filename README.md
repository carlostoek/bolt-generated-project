# Botmaestro - Sistema de Bot Multi-Tenant con Gamificación

## 🌟 Características Principales

### ✨ Experiencia de Usuario Mejorada
- **Gestión Inteligente de Mensajes**: Sin basura en el chat, mensajes temporales que se auto-eliminan
- **Navegación Fluida**: Menús que se actualizan sin crear nuevos mensajes
- **Interfaz Consistente**: Experiencia pulida y profesional en toda la aplicación
- **Sistema de Navegación**: Historial de navegación con funcionalidad de "volver"

### 🏢 Sistema Multi-Tenant
- **Configuración Independiente**: Cada administrador puede configurar su propio bot
- **Setup Guiado**: Proceso de configuración inicial paso a paso
- **Gestión de Canales**: Configuración separada de canales VIP y gratuitos
- **Tarifas Personalizadas**: Sistema de suscripciones configurable por tenant

### 🎮 Sistema de Gamificación Universal
- **Gamificación Lite para Usuarios Gratuitos**: Multiplicadores reducidos y funciones limitadas
- **Gamificación Completa para VIP**: Acceso total con multiplicadores mejorados
- **Sistema de Puntos Diferenciado**: Configuración automática según el tipo de usuario
- **Misiones y Recompensas**: Sistema completo de engagement

## 🚀 Configuración Inicial

### 1. Instalación de Dependencias

```bash
pip install -r requirements.txt
```

### 2. Variables de Entorno

```bash
export BOT_TOKEN="<your_bot_token>"
export ADMIN_IDS="11111;22222"          # IDs de usuarios administradores
export VIP_CHANNEL_ID="-100123456789"   # ID del canal VIP (opcional)
export FREE_CHANNEL_ID="-100987654321"  # ID del canal gratuito (opcional)
export DATABASE_URL="sqlite+aiosqlite:///gamification.db"  # Conexión a BD
export VIP_POINTS_MULTIPLIER="2"        # Multiplicador de puntos VIP
export CHANNEL_SCHEDULER_INTERVAL="30"  # Segundos entre verificaciones de canal
export VIP_SCHEDULER_INTERVAL="3600"    # Segundos entre verificaciones VIP
```

### 3. Inicialización de la Base de Datos

```bash
python scripts/init_db.py
```

### 4. Ejecutar el Bot

```bash
python mybot/bot.py
```

## 🛠️ Configuración Multi-Tenant

### Primer Uso (Administradores)

1. **Comando de Inicio**: Usa `/start` como administrador
2. **Setup Guiado**: El bot detectará que es la primera vez y ofrecerá configuración guiada
3. **Configuración de Canales**: 
   - Reenvía mensajes de tus canales para detectar automáticamente los IDs
   - O ingresa los IDs manualmente
4. **Configuración de Tarifas**: Crea planes de suscripción VIP
5. **Gamificación**: Configura el sistema de puntos y misiones

### Configuración Avanzada

Accede al panel de administración con `/admin_menu` para:
- Gestionar usuarios y suscripciones
- Crear misiones y recompensas personalizadas
- Configurar eventos y sorteos
- Administrar el sistema de subastas
- Personalizar mensajes y reacciones

## 👥 Roles y Flujos de Usuario

### 🔧 Administradores
- **Panel de Control Completo**: Gestión total del bot y configuraciones
- **Setup Multi-Tenant**: Configuración independiente por administrador
- **Gestión de Contenido**: Control sobre gamificación, canales y usuarios
- **Estadísticas**: Métricas detalladas de uso y engagement

### 💎 Usuarios VIP
- **Gamificación Completa**: Acceso total al sistema de puntos y recompensas
- **Multiplicadores Mejorados**: Puntos adicionales por actividades
- **Subastas Exclusivas**: Participación en subastas en tiempo real
- **Contenido Premium**: Acceso a canales y funciones exclusivas

### 🆓 Usuarios Gratuitos
- **Gamificación Lite**: Sistema reducido pero funcional
- **Multiplicadores Básicos**: Puntos estándar por actividades
- **Acceso Limitado**: Funciones básicas y canal gratuito
- **Upgrade Path**: Opciones claras para mejorar a VIP

## 🎯 Sistema de Gamificación

### Características Universales
- **Puntos por Actividad**: Mensajes, reacciones, check-ins diarios
- **Sistema de Niveles**: Progresión basada en puntos acumulados
- **Misiones Dinámicas**: Tareas diarias, semanales y especiales
- **Insignias y Logros**: Reconocimientos por hitos alcanzados
- **Ranking Global**: Competencia sana entre usuarios

### Diferenciación VIP vs Gratuito
- **Multiplicadores**: VIP 2x, Gratuito 1x (configurable)
- **Acceso a Recompensas**: VIP acceso completo, Gratuito limitado
- **Frecuencia de Misiones**: VIP más misiones disponibles
- **Subastas**: Solo VIP puede participar

## 🏛️ Sistema de Subastas (VIP)

### Características
- **Tiempo Real**: Subastas con temporizadores automáticos
- **Auto-extensión**: Extensión automática si hay pujas de último minuto
- **Notificaciones**: Alertas cuando otros usuarios superan tu puja
- **Historial**: Seguimiento de participación y resultados

### Gestión Administrativa
- **Creación Flexible**: Configuración completa de duración, precios y premios
- **Monitoreo**: Supervisión en tiempo real de todas las subastas
- **Finalización Manual**: Opción de terminar subastas anticipadamente
- **Estadísticas**: Métricas de participación y engagement

## 📊 Tareas Programadas

### Verificaciones Automáticas
1. **Solicitudes de Canal**: Aprobación automática después del tiempo de espera
2. **Suscripciones VIP**: Recordatorios de expiración y limpieza automática
3. **Subastas**: Finalización automática y notificaciones de resultados

### Configuración de Intervalos
- Modificables desde el panel de administración
- Variables de entorno para configuración inicial
- Logs detallados para monitoreo

## 🔧 Arquitectura del Sistema

### Gestión de Menús
- **MenuManager**: Gestión centralizada de mensajes y navegación
- **MenuFactory**: Creación consistente de menús basada en roles
- **Navegación Inteligente**: Historial y funcionalidad de "volver"
- **safe_answer / safe_edit**: Utiliza estas funciones para enviar mensajes de forma segura

### Servicios Multi-Tenant
- **TenantService**: Gestión de configuraciones independientes
- **ConfigService**: Almacenamiento de configuraciones por tenant
- **Aislamiento de Datos**: Cada administrador gestiona su propia instancia

### Base de Datos
- **SQLAlchemy Async**: ORM moderno para operaciones asíncronas
- **Migraciones Automáticas**: Creación automática de tablas en primer uso
- **Escalabilidad**: Diseño preparado para múltiples tenants

## 🚀 Preparación para Distribución Pública

### Características de Distribución
- **Setup Automático**: Configuración guiada para nuevos administradores
- **Aislamiento Completo**: Cada instancia es independiente
- **Documentación Integrada**: Guías y ayuda dentro del bot
- **Configuración Flexible**: Adaptable a diferentes necesidades

### Consideraciones de Seguridad
- **Validación de Permisos**: Verificación estricta de roles
- **Sanitización de Datos**: Limpieza automática de inputs
- **Envío Seguro de Mensajes**: Todas las respuestas utilizan `safe_answer` y `safe_edit` para evitar textos vacíos
- **Logs de Auditoría**: Registro detallado de acciones administrativas

## 📈 Métricas y Estadísticas

### Panel de Administración
- **Usuarios Totales**: Conteo de usuarios registrados
- **Suscripciones**: Activas, expiradas y ingresos
- **Engagement**: Participación en gamificación
- **Uso de Funciones**: Estadísticas de uso por característica

### Exportación de Datos
- **Reportes Automáticos**: Generación de reportes periódicos
- **Métricas en Tiempo Real**: Dashboard actualizado constantemente
- **Análisis de Tendencias**: Identificación de patrones de uso

## 🔄 Actualizaciones y Mantenimiento

### Versionado
- **Migraciones Automáticas**: Actualización de BD sin pérdida de datos
- **Compatibilidad**: Mantenimiento de compatibilidad hacia atrás
- **Rollback**: Capacidad de revertir cambios si es necesario

### Monitoreo
- **Logs Estructurados**: Sistema de logging detallado
- **Alertas Automáticas**: Notificaciones de errores críticos
- **Métricas de Rendimiento**: Monitoreo de performance del bot

## 📞 Soporte y Documentación

### Recursos Disponibles
- **Documentación Integrada**: Ayuda accesible desde el bot
- **Guías de Setup**: Tutoriales paso a paso
- **FAQ**: Preguntas frecuentes y soluciones

### Comunidad
- **Canal de Soporte**: Asistencia técnica
- **Actualizaciones**: Notificaciones de nuevas características
- **Feedback**: Canal para sugerencias y mejoras

---

## 🎉 ¡Listo para Usar!

Tu bot está ahora preparado para distribución pública con:
- ✅ Experiencia de usuario pulida y profesional
- ✅ Sistema multi-tenant completamente funcional
- ✅ Gamificación diferenciada para VIP y usuarios gratuitos
- ✅ Configuración guiada para nuevos administradores
- ✅ Gestión inteligente de mensajes sin basura en el chat
- ✅ Navegación fluida y consistente
- ✅ Sistema de subastas en tiempo real
- ✅ Arquitectura escalable y mantenible

¡Comienza con `/start` y disfruta de la experiencia mejorada!
