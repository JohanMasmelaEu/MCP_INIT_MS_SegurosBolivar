# Tech Stack Constraints — Seguros Bolivar

## Approved Runtimes
| Runtime | Version | Use Case |
|---------|---------|----------|
| Java | JDK 21 LTS | Backend with Spring Boot |
| Node.js | 20.x LTS | Backend with Express/Fastify |
| Python | 3.12+ | APIs with FastAPI, AI/ML |

## Backend (Java)
- Spring Boot 4.x
- Spring Data JPA (PostgreSQL)
- Spring Security (OAuth2 RS)
- Gradle 9.x

## Approved Database
- PostgreSQL 15+ (standard relational)
- H2 (test only)

## Forbidden Stacks
- Vue, Svelte, SolidJS, Next.js, Nuxt, Astro (frontend)
- NestJS, Go/Gin, Ruby on Rails, Django, Flask, .NET (backend)

## Dependency Registry
- All dependencies from JFrog Artifactory (institutional)
- Pin exact versions (no ^, *, latest)
