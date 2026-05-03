# PyMOL Collab Plugin

**PyMOL Collab** es un plugin diseñado para habilitar sesiones colaborativas en tiempo real dentro de PyMOL. Permite a múltiples investigadores visualizar, navegar y discutir estructuras moleculares simultáneamente, sin importar en qué parte del mundo se encuentren.

---

## 🌟 Características Principales

* **Sincronización en Tiempo Real:** El estado de la sesión, las representaciones y las moléculas cargadas por el anfitrión (Host) se sincronizan automáticamente con todos los usuarios conectados.
* **Seguimiento de Cámara:** Por defecto, los usuarios ven exactamente lo mismo que el Host. Es posible "desacoplarse" para explorar la molécula libremente y volver a sincronizarse con un clic.
* **Punteros y Selecciones:** Los usuarios conectados pueden seleccionar átomos o residuos de interés. Estas selecciones se resaltarán en las pantallas de todos los participantes con el nombre del usuario.
* **Traspaso de Control:** Cualquier usuario puede solicitar convertirse en el nuevo Host para realizar modificaciones en la sesión.
* **Privacidad por Diseño:** Las conexiones se realizan de punto a punto (P2P). No dependemos de servidores centrales que almacenen tus modelos moleculares.

---

## 🛠️ Instalación

1. Descarga la última versión del plugin desde la sección de **Releases** de este repositorio (archivo `.zip` o `.py`).
2. Abre PyMOL.
3. En el menú superior, ve a `Plugin` > `Plugin Manager`.
4. Ve a la pestaña `Install New Plugin`.
5. Selecciona `Choose file...`, busca el archivo descargado y haz clic en `Instalar`.
6. Reinicia PyMOL. Verás "PyMOL Collab" en el menú de Plugins.

---

## 🚀 Guía de Uso Rápido

### Crear una sesión (Ser el Host)
1. Abre el panel de **PyMOL Collab**.
2. Ingresa una contraseña segura (si la dejas en blanco, el plugin generará una por ti).
3. Haz clic en **"Iniciar Sesión"**.
4. Comparte tu Dirección IP y la contraseña (o el Código de Invitación) con tus colegas.

### Unirse a una sesión (Ser Viewer)
1. Abre el panel de **PyMOL Collab**.
2. Selecciona la pestaña **"Unirse a Sesión"**.
3. Ingresa la IP del Host y la contraseña, o pega el **Código de Invitación** proporcionado por el Host.
4. Haz clic en **"Conectar"**.

### Controles de la Interfaz
* **Seguir a [Usuario]:** Fija tu cámara a la vista de otro participante.
* **Exploración Libre:** Desvincula tu cámara para navegar por tu cuenta.
* **Solicitar ser Host:** Envía una notificación al Host actual para que te ceda el control de la sesión (ideal para cuando quieres cambiar colores, cargar nuevos modelos, etc.).
* **Desconectarse:** Finaliza la conexión de red, pero conserva todo el trabajo actual en tu PyMOL para que puedas seguir editando localmente.

---

## 🌐 Opciones de Conexión (¿Cómo conectarse con otros?)

Dado que el plugin funciona conectando las computadoras directamente sin usar servidores intermediarios que guarden tus datos, hemos preparado **tres métodos de conexión** que se adaptan a cualquier situación de red. ¡Todos son 100% gratuitos y no requieren crear cuentas!

### Opción 1: Conexión Automática (LAN / UPnP) - *La más fácil*
Ideal si están en la misma red local (oficina, laboratorio) o si tu router doméstico admite UPnP.
* **Cómo funciona:** Si están en la misma red, simplemente usa la IP local. Si están en diferentes redes a través de Internet, el plugin intentará comunicarse mágicamente con tu router para abrir una vía de comunicación temporal.
* **Pasos:** El Host presiona "Iniciar Sesión" y le pasa su **Dirección IP** y la **Contraseña** a los demás. ¡Eso es todo!

### Opción 2: Códigos de Invitación (WebRTC) - *Infalible contra bloqueos*
Ideal si la Opción 1 falla porque estás en la red estricta de una universidad o tu router bloquea conexiones.
* **Cómo funciona:** Utiliza una tecnología llamada "Hole Punching". Requiere que ambos usuarios se pasen un bloque de texto para "encontrarse" en internet.
* **Pasos:**
  1. El **Host** hace clic en *"Generar Código de Invitación"* y se lo envía al **Viewer** (por Slack, WhatsApp, email, etc.).
  2. El **Viewer** pega ese código en su PyMOL. Esto generará automáticamente un *"Código de Respuesta"*.
  3. El **Viewer** le envía ese Código de Respuesta al **Host**.
  4. El **Host** lo pega en su panel... ¡Y la conexión se establece al instante!

### Opción 3: Apertura Manual de Puertos (Avanzado)
Ideal para usuarios con conocimientos técnicos que desean hospedar sesiones recurrentemente.
* **Cómo funciona:** Requiere que el Host ingrese a la configuración de su router (usualmente escribiendo `192.168.1.1` o `192.168.0.1` en el navegador) y configure una regla de **Port Forwarding**.
* **Pasos:** Deberás redirigir el puerto TCP `5000` (o el que configures en el plugin) hacia la dirección IP local de tu computadora. Luego, simplemente tus colegas se conectan usando tu IP Pública y la contraseña, igual que en la Opción 1.

---

## 🔒 Seguridad
* **Encriptación:** Todas las conexiones realizadas a través de internet utilizando los métodos recomendados están cifradas para proteger la privacidad de tus estructuras y contraseñas.
* **Control Estricto:** El plugin está diseñado a prueba de Ejecución de Código Remoto (RCE). El Host es el único que puede ejecutar comandos mutativos que alteren el modelo base, y todo el tráfico de red está restringido a parámetros visuales y de estado predefinidos, nunca a comandos de terminal abiertos.
