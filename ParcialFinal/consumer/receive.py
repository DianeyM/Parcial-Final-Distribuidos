import pika   # Importa la librería pika para la conexión con RabbitMQ
import os     # Para acceder a variables de entorno (para la ruta del archivo)
import sys    # Para manejo de salida del programa
import time   # Para añadir una marca de tiempo a las entradas del log
from retry import retry # Para reintentar la conexión a RabbitMQ

# --- Configuración del archivo de log ---
# Define la ruta donde se guardarán los mensajes.
# Se obtiene de la variable de entorno MESSAGE_LOG_PATH o usa 'messages.log' por defecto.
MESSAGE_LOG_PATH = os.getenv("MESSAGE_LOG_PATH", "messages.log")
# ----------------------------------------

# Función que se ejecuta cada vez que se recibe un mensaje de la cola
def callback(ch, method, properties, body):
    try:
        # Decodifica el cuerpo del mensaje de bytes a una cadena de texto
        decoded_message = body.decode()
        print(f" [x] Mensaje recibido: {decoded_message}", flush=True)

        # --- Escribir el mensaje en el archivo de log local ---
        try:
            # Abre el archivo en modo de adición ('a') para añadir contenido al final
            with open(MESSAGE_LOG_PATH, 'a') as f:
                # Escribe el mensaje junto con una marca de tiempo
                f.write(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {decoded_message}\n")
            print(f" [!] Mensaje guardado en '{MESSAGE_LOG_PATH}'", flush=True)
        except IOError as file_error:
            # Manejo de errores si hay problemas al escribir en el archivo
            print(f" [!!!] Error al escribir en el archivo '{MESSAGE_LOG_PATH}': {file_error}", flush=True)
            # En caso de error de escritura, aún podemos reconocer el mensaje en RabbitMQ
            # para evitar que se reencole indefinidamente si el problema es persistente.

        # Reconoce (ack) el mensaje solo después de haber intentado escribirlo en el archivo.
        # Esto indica a RabbitMQ que el mensaje ha sido procesado.
        ch.basic_ack(delivery_tag=method.delivery_tag)
        print(" [x] Mensaje reconocido por RabbitMQ.\n", flush=True)

    except Exception as e:
        # Captura cualquier otra excepción durante el procesamiento del mensaje
        print(f"Error procesando mensaje: {e}", flush=True)
        # Rechazamos el mensaje. 'requeue=False' es útil para evitar bucles infinitos
        # si el mensaje es problemático, permitiendo usar una 'Dead Letter Queue' (DLQ).
        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)


# Función para conectarse a RabbitMQ con reintentos automáticos
@retry(tries=5, delay=2) # Reintenta hasta 5 veces, con 2 segundos de espera entre intentos
def connect_to_rabbitmq():
    # Obtiene las credenciales y el host de RabbitMQ desde variables de entorno
    rabbit_host = os.getenv("RABBIT_HOST", "localhost")
    rabbit_user = os.getenv("RABBIT_USER", "guest")
    rabbit_password = os.getenv("RABBIT_PASSWORD", "guest")

    # Configura los parámetros de conexión
    credentials = pika.PlainCredentials(rabbit_user, rabbit_password)
    connection_params = pika.ConnectionParameters(
        host=rabbit_host,
        credentials=credentials
    )

    # Establece y devuelve la conexión con RabbitMQ
    connection = pika.BlockingConnection(connection_params)
    return connection

# Función principal que configura la conexión y el consumo de mensajes
def main():
    try:
        # 1. Conecta a RabbitMQ, utilizando la lógica de reintentos
        connection = connect_to_rabbitmq()

        # 2. Crea un canal de comunicación
        channel = connection.channel()

        # 2.1 Limita la cantidad de mensajes que el consumidor puede tener pendientes de reconocimiento a la vez.
        # Esto es útil para la gestión de carga.
        channel.basic_qos(prefetch_count=1)

        # 3. Declara la cola 'messages'. Si no existe, la crea.
        # 'durable=True' asegura que la cola persista si el servidor RabbitMQ se reinicia.
        channel.queue_declare(queue='messages', durable=True)

        # 4. Configura el consumidor para que escuche la cola 'messages'.
        # 'auto_ack=False' significa que nosotros, en la función 'callback',
        # enviaremos la confirmación del mensaje manualmente.
        channel.basic_consume(
            queue='messages',
            auto_ack=False,
            on_message_callback=callback
        )

        # 5. Imprime un mensaje informando que el consumidor está esperando mensajes
        print(' [*] Esperando mensajes. Para salir presiona CTRL+C')

        # 6. Inicia el consumo de mensajes. Esto es un bucle infinito.
        channel.start_consuming()

    except pika.exceptions.AMQPConnectionError as connection_error:
        # Maneja los errores de conexión con RabbitMQ
        print(f" [!] Error al conectar con RabbitMQ: {connection_error}")
        sys.exit(1) # Sale del programa con un código de error

    except KeyboardInterrupt:
        # Captura la interrupción por teclado (Ctrl+C) para una salida limpia
        print(' [!] Interrumpido por el usuario')
        try:
            sys.exit(0) # Intenta una salida normal
        except SystemExit:
            os._exit(0) # Si la salida normal falla, fuerza la salida

# Asegura que main() se ejecute solo cuando el script se inicia directamente
if __name__ == '__main__':
    main()