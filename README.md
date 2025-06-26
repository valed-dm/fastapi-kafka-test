    Decoupled Services:

        Each Spider-Person (spidey_1, spidey_2, etc.) runs independently, communicating only via Kafka.

        No direct HTTP calls between services → true microservices architecture.

    Event-Driven Logic:

        /start triggers a Kafka event → all services react asynchronously.

        Services "compete" by passing the baton (Kafka messages) until a winner emerges.

    Scalability:

        Add more Spider-People? Just launch new instances with unique MY_NAME.

        Kafka’s consumer groups handle load balancing automatically.


To test:

```bash

docker compose up --build
```