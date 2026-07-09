# Code Style — Clean Code (Seguros Bolivar)

## Naming Conventions

| Element | Java |
|---------|------|
| Classes / Interfaces | PascalCase |
| Methods / Functions | camelCase |
| Variables | camelCase |
| Constants | UPPER_SNAKE_CASE |
| Booleans | `isActive`, `hasPermission` |
| Files | PascalCase (classes) |
| Packages | lowercase |

## Functions
- Maximum ~20 lines per function
- One function does one thing
- Maximum 3 parameters; use object for more
- Maximum cyclomatic complexity: 15

## Error Handling
- Specific errors, never bare catch
- Descriptive messages internally, generic to client
- Fail fast: validate early

## File Structure
- Group by domain/feature, not by technical type

## Testing
- Given / When / Then (Arrange / Act / Assert)
- Minimum 80% coverage
- Mock all external dependencies
