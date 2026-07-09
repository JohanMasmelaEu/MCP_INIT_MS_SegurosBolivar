# Blueprint Tecnico — Microservicio Java/Spring Boot (Seguros Bolivar)

> Documento de referencia para generacion automatizada de proyectos tipo microservicio.

---

## Stack Tecnologico

| Componente | Version |
|------------|---------|
| Java (JDK) | 21 LTS |
| Gradle | 9.4.1 |
| Spring Boot | 4.0.2 |
| Spring Dependency Management | 1.1.7 |
| PostgreSQL | 15+ |
| H2 (test) | runtime |

## Dependencias Clave

### Spring Boot Starters
- spring-boot-starter-actuator
- spring-boot-starter-data-jpa
- spring-boot-starter-security
- spring-boot-starter-security-oauth2-resource-server
- spring-boot-starter-validation
- spring-boot-starter-webmvc
- spring-boot-starter-webflux (WebClient)

### Documentacion API
- springdoc-openapi-starter-webmvc-ui:3.0.2

### AWS
- aws-java-sdk-ssm:1.12.722
- aws-java-sdk-secretsmanager:1.12.722
- aws-java-sdk-s3:1.12.722 (opcional)
- aws-java-sdk-sqs:1.12.722 (opcional)
- amazon-sqs-java-extended-client-lib:2.1.2 (opcional)

### Librerias Internas
- commons-gradle-error-handling-java:1.0.0.RELEASE
- bolivar-centralizador-logs:1.0.0.RELEASE

### Testing
- JUnit 5 (via spring-boot-starter-test)
- WireMock JRE8:2.35.2
- JaCoCo 0.8.14 (min 85% lineas)

---

## Arquitectura de Paquetes (Domain-Driven)

```
com.bolivar.<artifact>/
├── Application.java
├── Configuration.java
├── commons/           (ApiResponseDTO, ApiResponseData, ApiResponseMensajes)
├── config/            (DB, SSM, OpenAPI, WebClient, Security)
│   └── security/      (SecurityConfig, filtros, handlers)
├── entity/            (JPA entities + MappedSuperclass auditoria)
├── errorhandling/     (BolivarBusinessException, GlobalExceptionHandler)
├── utils/             (DataSanitizer, HtmlEntityEncoder)
└── <dominio>/         (controller/, dto/, services/, repository/)
```

## Patrones de Implementacion

### Respuesta API
```json
{"codigo": "OK", "mensaje": "Operacion exitosa", "data": {...}}
```

### Excepcion de Negocio
```java
throw BolivarBusinessException.builder()
    .codigo("ENTIDAD_NO_ENCONTRADO")
    .mensaje("Descripcion")
    .categoria(TipoErrorEnum.NEGOCIO)
    .build();
```

### Entity JPA
- Extiende AuditoriaCompleta (4 campos auditoria)
- Schema dedicado en PostgreSQL
- GenerationType.IDENTITY para IDs
- Campo cod_<entidad> autogenerado (patron CUC)

### Controller
- @RestController + @RequestMapping("/api/v1/<recurso>")
- @Tag + @Operation (OpenAPI)
- ResponseEntity<ApiResponseDTO<T>>

### Service
- Interface + Impl (@Service, @Transactional)
- Inyeccion por constructor (@RequiredArgsConstructor)

### Repository
- JpaRepository + JpaSpecificationExecutor
- Specification para filtros dinamicos

---

## Infraestructura Local

- Docker Compose: LocalStack (SSM, S3, SQS) + Mock OAuth + Datadog Agent (no-forward)
- Perfiles: local (PostgreSQL via SSM), test (H2)
- CI/CD: GitHub Actions con templates institucionales

---

## Seguridad

- Spring Security con estrategia pluggable (OAuth2 RS, API GW, M2M, deferred)
- Headers: HSTS, X-Content-Type-Options, X-Frame-Options, Referrer-Policy
- Sanitizacion XSS en respuestas (HTML entities)
- Secrets via AWS SSM Parameter Store (nunca en codigo)

---

*Generado por MCP_INIT_MS_SegurosBolivar v1.0.0*
