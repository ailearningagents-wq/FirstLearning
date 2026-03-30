# ASP.NET Core MVC → Angular + Web API Migration Plan

## Workspace Modification Permission

Before starting any migration work, ask the user:

**"This migration will create, modify, and reorganize files across your Angular and Web API projects. Do you grant permission to modify your workspace for the entire migration operation? (yes/no)"**

- If **yes** — Proceed with all file creation, modification, and reorganization steps throughout the entire migration without asking for permission again at each individual step.
- If **no** — Ask for explicit confirmation before each file creation, modification, or deletion during the migration process.

Do not proceed with any migration phases until this permission is granted or denied.

---

## Project Paths

Ask the user for each path one at a time. Do not proceed to the next question until the current path is provided and validated:

1. First, ask: **"Please provide the full path to the Source ASP.NET Core MVC project:"** — Wait for response, validate the path exists and contains a `.csproj` file.
2. Then ask: **"Please provide the full path to the Destination Angular project:"** — Wait for response, validate the path exists and contains a `package.json` and `angular.json`.
3. Then ask: **"Please provide the full path to the Destination C# Web API project:"** — Wait for response, validate the path exists and contains a `.csproj` file.

Do not proceed with any migration until all three paths are collected and validated.

4. Then ask: **"Does the source MVC application use Kendo UI? (yes/no):"** — If yes, use Kendo Angular components for UI migration. If no, skip Phase 4 and use standard HTML/Angular Material controls based on what's installed in the destination Angular project.

## Overview

Migrate monolithic MVC app into: **Angular** (existing project, UI) + **C# Web API** (existing project, backend). Packages, CORS, auth already configured in both projects.

### Pre-Migration: Analyze Destination Projects First

Before generating any code, **analyze both destination projects** to understand:

**Angular Project:**
- Existing folder structure, module organization (standalone vs NgModule), routing setup
- Installed packages (`package.json`) — identify Kendo Angular, Angular Material, Bootstrap, ngx-toastr, etc.
- Existing shared/core modules, interceptors, guards, services already in place
- Coding conventions — naming patterns, file organization, state management approach
- Angular version and syntax style (e.g., control flow `@if`/`@for` vs `*ngIf`/`*ngFor`)
- Existing environment config files and API URL setup

**Web API Project:**
- Existing folder structure, namespace conventions, project layers
- Installed packages (`.csproj`) — identify EF Core, AutoMapper, FluentValidation, MediatR, etc.
- Existing middleware pipeline, DI registrations in `Program.cs`/`Startup.cs`
- Existing base classes, shared DTOs, response wrappers, error handling patterns
- Auth configuration already in place (JWT, Identity, policies)
- Existing DbContext, entity configurations, migration history

**All generated code must follow the destination project's existing patterns, conventions, and folder structure. Do not impose a new structure — adapt to what is already there.**

### Migration Must Include

- **All server-side validations** — Data annotations, FluentValidation rules, custom `IValidatableObject` implementations, action filter validations → migrate to both API DTOs (server-side) and Angular Reactive Forms (client-side)
- **All client-side validations** — jQuery Unobtrusive Validation, custom JS validators → Angular form validators (built-in + custom `ValidatorFn` / `AsyncValidatorFn`)
- **AutoMapper profiles** — All entity↔ViewModel mappings → entity↔DTO AutoMapper profiles in Web API
- **Custom middleware** — Exception handling, request logging, tenant resolution, rate limiting, etc. → Web API middleware pipeline
- **Custom action filters** — Authorization filters, validation filters, audit filters → Web API `IActionFilter` / `IAsyncActionFilter` / middleware
- **Custom exception filters** — `IExceptionFilter` implementations → Web API exception handling middleware or filters
- **Custom result filters** — `IResultFilter` implementations → Web API equivalent filters
- **Custom model binders** — `IModelBinder` implementations → Web API custom model binders or `[FromBody]`/`[FromQuery]` with DTOs
- **Custom tag helpers** — Server-side tag helpers → Angular directives or Kendo Angular components
- **Custom HTML helpers** — `@Html.CustomHelper()` → Angular pipes, directives, or components
- **Custom validation attributes** — `[CustomValidation]`, `ValidationAttribute` subclasses → API: custom validation attributes on DTOs + Angular: custom validator functions
- **Business rule validations** — Service-layer validations, domain validations → preserve in Web API services, surface errors via `ProblemDetails` to Angular
- **All DbContext classes & EF Core configuration** — Migrate every DbContext, entity configurations, seeding, and migrations into the destination Web API project following its existing data layer structure

---

## Phase 1: Analyze Source MVC App

Inventory all: Controllers (actions, routes, `[Authorize]`), Razor Views (layouts, partials, tag helpers), View Models, EF Core entities/DbContext, Services, Static assets, Third-party libs (Kendo etc.), Middleware/Filters, Custom Validations, AutoMapper profiles, SignalR hubs, Background jobs.

**Library Mapping:**

| MVC Library | Angular Equivalent |
|---|---|
| Kendo UI / Telerik | `@progress/kendo-angular-*` |
| Bootstrap | `ngx-bootstrap` / `@ng-bootstrap/ng-bootstrap` |
| jQuery Validation | Angular Reactive Forms |
| DataTables | Kendo Grid / Material Table |
| Select2 | Kendo DropDownList / Material Autocomplete |
| Chart.js/Highcharts | Kendo Charts / `ngx-charts` |
| Toastr / SweetAlert | `ngx-toastr` / `sweetalert2` |

---

## Phase 2: Backend — MVC Controllers → Web API

### Controller Conversion Rules

- `Controller` → `ControllerBase` with `[ApiController]`, `[Route("api/[controller]")]`
- `return View(...)` → `return Ok(...)` (JSON responses)
- `RedirectToAction(...)` → proper status codes (`CreatedAtAction`, `NoContent`, `NotFound`, `BadRequest`)
- Remove `[ValidateAntiForgeryToken]` (JWT handles security); preserve `[Authorize]` attributes
- `[ApiController]` auto-validates ModelState; remove manual `ModelState.IsValid` checks
- ViewModels → DTOs, mapped via AutoMapper profiles

### Per-Controller Steps

1. Create API controller following **destination project's existing controller conventions**
2. Move/adapt Service interfaces & implementations into destination's service layer structure
3. Move Entity models + DbContext into destination's data layer, update connection string
4. Create DTOs following destination's existing DTO patterns; add AutoMapper profiles to existing profile structure
5. Migrate all validations (data annotations, FluentValidation, custom attributes) to DTOs
6. Migrate custom action/exception/result filters into destination's filter or middleware structure
7. Migrate custom model binders if applicable
8. Register all services in DI following destination's existing registration pattern

### DbContext & EF Core Migration

Migrate **all** DbContext classes and EF Core data layer into the destination Web API project:

1. **Analyze destination's existing data layer** — Check if a DbContext already exists, its location, namespace, and configuration style (Fluent API vs data annotations, `OnModelCreating` vs separate `IEntityTypeConfiguration<T>` classes)
2. **Migrate all entity models** — Copy all EF Core entity classes into destination's entity/model folder, preserving relationships, navigation properties, and data annotations
3. **Migrate DbContext classes** — If source has a single DbContext, merge its `DbSet<>` properties and configurations into destination's existing DbContext. If source has multiple DbContexts (e.g., `ApplicationDbContext`, `IdentityDbContext`, `TenantDbContext`), migrate each one respecting destination's pattern
4. **Migrate entity configurations** — Move all `IEntityTypeConfiguration<T>` classes or `OnModelCreating` Fluent API configurations into destination's configuration folder/structure
5. **Migrate seed data** — Move `HasData()` seed configurations or custom `IDbSeeder` classes
6. **Migrate repository layer** — If source uses Repository/Unit of Work pattern, move repositories into destination's existing repository structure. If destination uses DbContext directly, adapt accordingly
7. **Update connection strings** — Update `appsettings.json` / `appsettings.Development.json` with correct connection strings
8. **Regenerate migrations** — Create a fresh initial migration in the destination project (`dotnet ef migrations add InitialMigration`) or migrate existing migration history
9. **Migrate query filters** — Global query filters (soft delete, tenant isolation) from `OnModelCreating`
10. **Migrate interceptors** — EF Core `SaveChangesInterceptor`, `DbCommandInterceptor` for audit trails, soft delete, etc.
11. **Register DbContext in DI** — Follow destination's existing registration pattern (`AddDbContext`, `AddDbContextPool`, `AddDbContextFactory`)

### Auth Verification

Verify JWT Bearer, Role/Policy `[Authorize]` attributes, and claims mapping match the MVC app.

---

## Phase 3: Frontend — Razor Views → Angular

### Razor → Angular Mapping

| Razor | Angular |
|---|---|
| `_Layout.cshtml` | App shell + shared header/sidebar/footer (match destination layout) |
| `@model ViewModel` | TypeScript interface |
| `@Html.TextBoxFor` | `<input formControlName>` / Kendo textbox (use what's installed) |
| `@Html.DropDownListFor` | Kendo dropdownlist / Material select (use what's installed) |
| `@Html.ValidationMessageFor` | Angular form error display (match destination pattern) |
| `<form asp-action>` | `<form [formGroup] (ngSubmit)>` |
| `@Html.Partial("_X", item)` | Child component with `@Input` |
| `@Html.ActionLink` | `<a [routerLink]>` |
| `@if / @foreach` | `*ngIf`/`*ngFor` or `@if`/`@for` (match destination's Angular version) |
| `ViewBag.Title` | Title service |
| `TempData["Msg"]` | Notification service (use what's installed in destination) |
| `@Html.AntiForgeryToken()` | Not needed (JWT) |
| Kendo Tag Helpers | Kendo Angular components (if installed in destination) |

### Per-View Steps

1. **Analyze destination project** — identify existing component structure, module pattern, service pattern
2. Create TypeScript model/interface matching the API DTO
3. Create Angular service using HttpClient — follow destination's existing service patterns (base URL config, error handling)
4. Create components (list, detail, create/edit) — follow destination's existing component conventions
5. Add routing — follow destination's existing routing pattern (lazy-loaded modules or standalone routes)
6. Migrate all form validations — match destination's form validation approach (reactive forms, template forms, or existing custom validators)
7. Use third-party controls **only if already installed** in destination (Kendo Angular, Material, etc.)
8. Migrate CSS/styles into destination's styling approach (SCSS, CSS modules, global styles)

### Static Assets

Move `wwwroot/css/` → destination's styles location, `wwwroot/images/` → destination's assets location. Remove jQuery. Use destination's existing asset pipeline.

---

## Phase 4: Kendo Control Migration (If Installed in Destination)

Only apply if `@progress/kendo-angular-*` packages exist in destination's `package.json`:

| MVC Kendo | Angular Kendo |
|---|---|
| `Html.Kendo().Grid<T>()` | `<kendo-grid>` |
| `Html.Kendo().DropDownList()` | `<kendo-dropdownlist>` |
| `Html.Kendo().DatePicker()` | `<kendo-datepicker>` |
| `Html.Kendo().NumericTextBox()` | `<kendo-numerictextbox>` |
| `Html.Kendo().Chart()` | `<kendo-chart>` |
| `Html.Kendo().Upload()` | `<kendo-upload>` |
| `Html.Kendo().Window()` | `<kendo-dialog>` / `DialogService` |
| `Html.Kendo().TabStrip()` | `<kendo-tabstrip>` |
| `Html.Kendo().TreeView()` | `<kendo-treeview>` |
| `Html.Kendo().Editor()` | `<kendo-editor>` |

For server-side grid operations, use `[FromBody] DataSourceRequest` + `ToDataSourceResultAsync()` on the API side.

---

## Phase 5: Per-Controller Checklist

- [ ] API Controller (follow destination conventions)
- [ ] Services + Interfaces (follow destination service layer)
- [ ] DTOs + AutoMapper profile (follow destination DTO patterns)
- [ ] All validations migrated (server-side + client-side)
- [ ] Custom middleware/filters migrated
- [ ] DbContext, entities, configurations, seed data migrated
- [ ] EF Core interceptors, query filters migrated
- [ ] Migrations regenerated, connection strings updated
- [ ] Register services + DbContext in DI
- [ ] TypeScript models/interfaces
- [ ] Angular Service (follow destination service pattern)
- [ ] List, Detail, Create/Edit components (follow destination component pattern)
- [ ] Feature routing (follow destination routing pattern)
- [ ] Migrate third-party controls (only what's installed)
- [ ] Migrate CSS/styles
- [ ] E2E test full flow

**Order:** Core/Auth first → Simplest CRUD feature → Remaining features → Complex features (SignalR, file uploads)

---

## Quick Reference: Key Transformations

| MVC | Distributed |
|---|---|
| `Controller : Controller` → Views | `ControllerBase` → JSON |
| `.cshtml` Razor Views | Angular Components (`.ts`+`.html`) |
| ViewModels | DTOs (API) + TS Interfaces (Angular) |
| `@Html` helpers | Angular directives / Kendo Angular |
| `[ValidateAntiForgeryToken]` | JWT Bearer (interceptor) |
| `ModelState` | `[ApiController]` auto-validation + Angular forms |
| `RedirectToAction` | `router.navigate()` |
| `TempData` / `ViewBag` | Services / Notification library |
| Partial Views | Child components (`@Input`/`@Output`) |
| `_Layout.cshtml` | App shell + shared layout components |
| jQuery / vanilla JS | RxJS, directives, pipes |
| Session state | JWT claims / state management |
| Custom Filters | API Filters / Middleware |
| FluentValidation / DataAnnotations | API DTOs + Angular form validators |
| AutoMapper profiles | Updated AutoMapper profiles for DTOs |
| DbContext / EF Core entities | Migrated into destination's data layer |
| EF Core configurations / seed data | `IEntityTypeConfiguration<T>` / `HasData()` in destination structure |
| EF Core interceptors / query filters | Destination middleware / DbContext overrides |