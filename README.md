# Parcial-Final-Distribuidos


 CONCEPTOS TEÓRICOS
 
RabbitMQ 

● Explique qué es RabbitMQ y cuándo se debe utilizar una cola frente a un exchange tipo fanout.


 RabbitMQ es un broker de mensajes; un broker de mensajes (o message broker) es un intermediario que gestiona la comunicación de mensajes entre servicios o aplicaciones. Su propósito principal es desacoplar el emisor del receptor, permitiendo que cada uno funcione de forma independiente y asincrónica. 

En una arquitectura distribuida, donde distintos servicios corren en contenedores separados, RabbitMQ permite que un servicio envíe un mensaje (evento) y que otro lo reciba más tarde, aunque no estén disponibles al mismo tiempo. 

Con RabbitMQ el transporte de datos se hace por medio de mensajes (JSON, texto plano, binario, etc.) y no a través de solicitudes HTTP (REST, GraphQL, etc.) como lo hace Traefik. Además, RabbitMQ permite la persistencia de datos, en contraste con Traefik que solo enruta y no guarda datos.

La cola se emplea cuando no se requiere que los mensajes lleguen a todos los consumidores, esto sucede por ejemplo cuando se necesita balanceo de carga. En cambio el exchange tipo fanout se emplea si es  necesario o estratégico que todos los consumidores obtengan los mismos mensajes. 

● ¿Qué es una Dead Letter Queue (DLQ) y cómo se configura en RabbitMQ? 

Una cola de mensajes fallido es una cola en donde se disponen los mensajes que por algún motivo no pudieron ser procesados. 

Para configurarla se debe:

Crear la cola (queue: my-dead-letter-queue).
Se debe crear un exchange DLX (Dead Letter Exchange): exchange: my-dlx (tipo `direct` o `topic`)
Se debe vincular la cola DLQ al exchange DLX con routing_key='dead':
channel.queue_bind(
    		exchange='my-dlx',
    		queue='my-dead-letter-queue',
    		routing_key='dead'
)
Se debe configurar la cola original con políticas o argumentos. Ejemplo en Python con pika:
 	channel.queue_declare(
    		queue='main-queue',
    		arguments={
       			'x-dead-letter-exchange': 'my-dlx',
        			'x-dead-letter-routing-key': 'dead'
    		}
)

Docker y Docker Compose 

● Diferencia entre un volumen y un bind mount con ejemplos. 

Los volúmenes son gestionados directamente por Docker y se almacenan en /var/lib/docker/volumes/. Los bind mount enlazan archivos de la máquina host con los contenedores, permitiendo establecer la ubicación de los archivos tanto en el host como en el contenedor.  

Ejemplo de volumen: 


volumes:
  pgdata:
----------------
services:
  postgres:
    image: postgres
    volumes:
      - pgdata:/var/lib/postgresql/data

Ejemplo de bind mount: 
services:
  api:
    build: .
    volumes:
      - ./src:/app/src  # Carpeta local -> carpeta del contenedor


● ¿Qué implica usar network_mode: host en un contenedor?

Implica que los contenedores que se conecten a este tipo de red, deben estar en el mismo equipo host; fuera del host no habrá comunicación. 

1.3 Traefik 
● Función de Traefik en una arquitectura de microservicios. 

Su rol principal es enrutar tráfico HTTP a múltiples servicios que pueden estar en contenedores, diferentes puertos, o incluso diferentes máquinas, detectando automáticamente los servicios y balanceando la carga entre ellos. 

● ¿Cómo se puede asegurar un endpoint usando certificados TLS automáticos en Traefik? 

Para asegurar un endpoint con certificados TLS automáticos en Traefik, se puede usar usar Let's Encrypt integrado en Traefik. Esto permite que Traefik obtenga y renueve automáticamente los certificados TLS, sin intervención manual.
