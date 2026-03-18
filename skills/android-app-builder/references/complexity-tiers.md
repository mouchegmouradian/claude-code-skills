# Complexity Tiers

This document defines the three architecture tiers used by the Android app builder skill.
When SKILL.md detects a tier, it refers here for the complete blueprint.

## Table of Contents

1. [Tier Decision Matrix](#tier-decision-matrix)
2. [Tier 1 — Simple](#tier-1--simple)
3. [Tier 2 — Standard](#tier-2--standard)
4. [Tier 3 — Production](#tier-3--production)
5. [Detection Heuristics (Extended)](#detection-heuristics-extended)
6. [Migration Paths](#migration-paths)

---

## Tier Decision Matrix

| Signal | Tier 1 — Simple | Tier 2 — Standard | Tier 3 — Production |
|---|---|---|---|
| Feature count | 1–3 | 3–6 | 6+ |
| Inter-feature data sharing | None | Some (shared repo) | Complex (multiple repos, use cases) |
| Persistence | In-memory or DataStore | Room optional | Room required |
| Background work | None | None | WorkManager |
| Team size | Solo / personal | 1–3 devs | 4+ / multiple teams |
| Build speed optimization | Not needed | Not needed | Required (incremental modules) |
| DI framework | None (factory pattern) | Hilt + KSP | Hilt + KSP |
| Module count | 1 | 1 | 5–20+ |
| Convention plugins | No | No | Yes (`build-logic/`) |
| Prototype / demo | Yes → Tier 1 | Possible | No |

---

## Tier 1 — Simple

### When to Use

- Personal apps, demos, prototypes, learning projects
- 1–3 features where no feature needs data from another feature
- Solo developer
- Time-to-first-screen matters more than long-term maintainability

### What You Get

- Single `app/` Gradle module
- No Hilt — ViewModel created via companion object factory
- No Room — use DataStore Preferences for persistence, or plain in-memory `MutableStateFlow`
- No `build-logic/` convention plugins
- String-based navigation routes (simpler to read at this scale)
- Repository is a concrete class; no interface required for simple cases

### What You Do NOT Get (by Design)

- Hilt DI graph
- Room database
- Multi-module structure (`feature/`, `core/`)
- `build-logic/` convention plugins
- Type-safe `@Serializable` routes (fine to add manually if desired)

### File Structure

```
app/
├── build.gradle.kts              # Direct plugin declarations, no convention plugins
└── src/main/kotlin/com/example/app/
    ├── MainActivity.kt
    ├── AppNavigation.kt           # NavHost + all routes in one file
    ├── data/
    │   └── MyRepository.kt        # Concrete class, no interface required
    └── ui/
        └── featurename/
            ├── FeatureNameRoute.kt
            ├── FeatureNameScreen.kt
            ├── FeatureNameViewModel.kt
            └── FeatureNameUiState.kt
```

### ViewModel Factory Pattern (No Hilt)

```kotlin
class FeatureNameViewModel(
    private val repository: MyRepository,
) : ViewModel() {

    val uiState: StateFlow<FeatureNameUiState> = repository
        .getData()
        .map { data -> FeatureNameUiState.Success(data) }
        .stateIn(
            scope = viewModelScope,
            started = SharingStarted.WhileSubscribed(5_000),
            initialValue = FeatureNameUiState.Loading,
        )

    fun onAction(action: FeatureNameAction) {
        when (action) {
            is FeatureNameAction.ItemClicked -> handleItemClick(action.id)
        }
    }

    companion object {
        fun factory(repository: MyRepository): ViewModelProvider.Factory =
            viewModelFactory {
                initializer { FeatureNameViewModel(repository) }
            }
    }
}
```

### Route Pattern (No `hiltViewModel()`)

```kotlin
@Composable
internal fun FeatureNameRoute(
    onNavigateToDetail: (String) -> Unit,
    repository: MyRepository,
    viewModel: FeatureNameViewModel = viewModel(
        factory = FeatureNameViewModel.factory(repository)
    ),
) {
    val uiState by viewModel.uiState.collectAsStateWithLifecycle()
    FeatureNameScreen(
        uiState = uiState,
        onAction = viewModel::onAction,
        onNavigateToDetail = onNavigateToDetail,
    )
}
```

### Repository Pattern (DataStore, No Interface)

```kotlin
class MyRepository(
    private val dataStore: DataStore<Preferences>,
) {
    val items: Flow<List<MyItem>> = dataStore.data
        .map { prefs -> prefs[MY_ITEMS_KEY]?.let { deserialize(it) } ?: emptyList() }

    suspend fun addItem(item: MyItem) {
        dataStore.edit { prefs ->
            val current = prefs[MY_ITEMS_KEY]?.let { deserialize(it) } ?: emptyList()
            prefs[MY_ITEMS_KEY] = serialize(current + item)
        }
    }

    companion object {
        val MY_ITEMS_KEY = stringPreferencesKey("my_items")
    }
}
```

### MainActivity Wiring (No Application subclass needed)

```kotlin
class MainActivity : ComponentActivity() {

    private val repository by lazy {
        MyRepository(applicationContext.dataStore)
    }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContent {
            AppTheme {
                AppNavigation(repository = repository)
            }
        }
    }
}

val Context.dataStore: DataStore<Preferences> by preferencesDataStore(name = "app_data")
```

### Navigation (String Routes, All in One File)

```kotlin
@Composable
fun AppNavigation(repository: MyRepository) {
    val navController = rememberNavController()
    NavHost(
        navController = navController,
        startDestination = "feature_name",
    ) {
        composable("feature_name") {
            FeatureNameRoute(
                onNavigateToDetail = { id -> navController.navigate("detail/$id") },
                repository = repository,
            )
        }
        composable("detail/{id}") { backStackEntry ->
            val id = backStackEntry.arguments?.getString("id") ?: return@composable
            DetailRoute(id = id, repository = repository)
        }
    }
}
```

> Tier 1 uses string routes for simplicity. Tier 2/3 use type-safe `@Serializable` routes.

### `build.gradle.kts` (Tier 1 — No KSP, No Hilt)

```kotlin
plugins {
    id("com.android.application")
    id("org.jetbrains.kotlin.plugin.compose")
}

android {
    namespace = "com.example.app"
    compileSdk = 36

    defaultConfig {
        applicationId = "com.example.app"
        minSdk = 26
        targetSdk = 36
        versionCode = 1
        versionName = "1.0"
    }

    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
    }

    buildFeatures {
        compose = true
    }
}

dependencies {
    implementation(platform(libs.androidx.compose.bom))
    implementation(libs.androidx.compose.ui)
    implementation(libs.androidx.compose.material3)
    implementation(libs.androidx.compose.ui.tooling.preview)
    implementation(libs.androidx.activity.compose)
    implementation(libs.androidx.navigation.compose)
    implementation(libs.androidx.lifecycle.viewmodel.compose)
    implementation(libs.androidx.lifecycle.runtime.compose)
    implementation(libs.androidx.datastore.preferences)
    debugImplementation(libs.androidx.compose.ui.tooling)
}
```

No `build-logic/`, no `ksp`, no Hilt compiler. This is intentional.

### Testing (Tier 1)

- ViewModel: construct directly with a fake repository (concrete subclass or implement a simple interface)
- No `TestDispatcherRule` needed unless coroutines are complex — use `runTest { }` directly
- Screen: pass plain data objects to the Screen composable in isolation
- No Hilt test setup

### Graduation Trigger → Tier 2

Move to Tier 2 when:
- You need to inject the same repository into more than 2 ViewModels, **or**
- You add a 4th feature that shares data with an existing feature, **or**
- You want Hilt-based integration tests

---

## Tier 2 — Standard

### When to Use

- Real apps with 3–6 features
- Small team (1–3 devs)
- Some features share a repository (e.g., user profile used on home + settings)
- Persistence required (Room)
- Needs proper DI for testability, but no need for module isolation

### What You Get

- Single `app/` Gradle module with feature packages
- Hilt for DI (KSP required)
- Room for persistence when needed
- `hiltViewModel()` in Route composables
- Type-safe `@Serializable` navigation routes
- Interface + implementation repository pattern
- Single `AppModule.kt` for Hilt bindings

### What You Do NOT Get (by Design)

- `build-logic/` convention plugins
- Multi-module structure (`feature/api`, `feature/impl`, `core/*`)
- WorkManager (add only if explicitly required)

### File Structure

```
app/
├── build.gradle.kts
└── src/main/kotlin/com/example/app/
    ├── MainActivity.kt              # @AndroidEntryPoint
    ├── AppNavigation.kt
    ├── di/
    │   └── AppModule.kt             # @Module @InstallIn(SingletonComponent)
    ├── model/
    │   └── MyModel.kt
    ├── data/
    │   ├── MyRepository.kt          # Interface
    │   └── MyRepositoryImpl.kt      # @Inject constructor
    └── ui/
        └── featurename/
            ├── FeatureNameRoute.kt  # hiltViewModel()
            ├── FeatureNameScreen.kt
            ├── FeatureNameViewModel.kt  # @HiltViewModel @Inject constructor
            └── FeatureNameUiState.kt
```

### `build.gradle.kts` (Tier 2 — Hilt + KSP, No Convention Plugins)

```kotlin
plugins {
    id("com.android.application")
    id("org.jetbrains.kotlin.plugin.compose")
    id("com.google.devtools.ksp")
    id("dagger.hilt.android.plugin")
}

android {
    namespace = "com.example.app"
    compileSdk = 36

    defaultConfig {
        applicationId = "com.example.app"
        minSdk = 26
        targetSdk = 36
        versionCode = 1
        versionName = "1.0"
    }

    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
    }

    buildFeatures {
        compose = true
    }
}

dependencies {
    implementation(platform(libs.androidx.compose.bom))
    implementation(libs.androidx.compose.ui)
    implementation(libs.androidx.compose.material3)
    implementation(libs.androidx.compose.ui.tooling.preview)
    implementation(libs.androidx.activity.compose)
    implementation(libs.androidx.navigation.compose)
    implementation(libs.androidx.lifecycle.viewmodel.compose)
    implementation(libs.androidx.lifecycle.runtime.compose)
    implementation(libs.hilt.android)
    ksp(libs.hilt.android.compiler)
    implementation(libs.androidx.hilt.navigation.compose)
    // Add Room only if persistence is needed:
    // implementation(libs.room.runtime)
    // implementation(libs.room.ktx)
    // ksp(libs.room.compiler)
    debugImplementation(libs.androidx.compose.ui.tooling)
}
```

No `build-logic/`, no multi-module, no convention plugins. Uses `hiltViewModel()` in Route
composables. Repositories are interfaces bound in a single `AppModule.kt`.

### Testing (Tier 2)

- ViewModel: construct directly with a fake repository implementing the interface (same as Tier 1)
- Can use `@HiltAndroidTest` for integration tests if desired, but constructor injection tests are preferred for speed
- Screen: pass plain data objects to the Screen composable in isolation

### Graduation Trigger → Tier 3

Move to Tier 3 when:
- Team grows beyond 3 developers needing independent feature work, **or**
- Feature count exceeds 6 with complex cross-feature data flows, **or**
- Build times become long enough to warrant incremental compilation boundaries, **or**
- You need independent module delivery or feature flags at module level

---

## Tier 3 — Production

### When to Use

This is the default for large-scale apps. Fully documented in the main SKILL.md and the
other reference files in this directory.

### Quick Summary

- Full NowInAndroid multi-module: `feature/api` + `feature/impl` + `core/*`
- `build-logic/` with convention plugins
- Hilt, Room, WorkManager
- 6+ features, multiple teams
- Gradle module boundaries enforce architectural rules and enable incremental compilation

### Full Documentation

- [modularization.md](modularization.md) — module types, dependency rules, creating modules
- [architecture.md](architecture.md) — data layer, domain layer, UI layer
- [gradle-setup.md](gradle-setup.md) — convention plugins, version catalog
- [testing.md](testing.md) — test doubles, integration tests

---

## Detection Heuristics (Extended)

These are the full reasoning rules. For the condensed version used during quick classification,
see `## Step 0: Detect Complexity Tier` in SKILL.md.

### Vocabulary Signals → Tier 1

- "demo", "prototype", "sample", "personal", "learning", "for fun", "side project", "proof of concept"
- "simple app", "basic app", "quick app"
- Single-screen or tab bar where each tab is fully independent (no shared data)
- No mention of teams, users, deployment, or backend
- Describes themselves as a beginner or student

### Vocabulary Signals → Tier 2

- "small app", "production but not complex", "startup MVP", "team of two"
- Mentions a backend or API ("fetch from my server", "sync with Firebase")
- Multiple screens referencing the same data model ("list and detail for the same items")
- "I want to use Hilt" — explicit request overrides heuristics

### Vocabulary Signals → Tier 3

- "NowInAndroid", "multi-module", "clean architecture", "modular"
- "multiple teams", "large codebase", "enterprise", "feature flags"
- "WorkManager for background sync", "offline-first with multiple repositories"
- Describes explicit module boundaries or "I want the architecture to scale"

### Edge Cases

| Description | Tier | Reason |
|---|---|---|
| "I want to learn Android architecture" | 1 | Start simple; graduate as learning progresses |
| "Build me a to-do app" (no context) | Ask | Could be Tier 1 (personal) or Tier 2 (synced/team) |
| "Build me Twitter" | 3 | Social feed, notifications, media, multiple teams implied |
| "Build me a calculator" | 1 | Unconditionally simple |
| Small app but user explicitly requests Hilt | 2 | Honor explicit request; note the decision |
| "An app with 4 features but they're totally independent" | 1 or 2 | Ask: do features share any repository or model? |

---

## Migration Paths

### Tier 1 → Tier 2 (Adding Hilt)

Steps in order:

1. Add plugins to `app/build.gradle.kts`: `com.google.devtools.ksp` and `dagger.hilt.android.plugin`
2. Add dependencies: `hilt-android`, `ksp(hilt-android-compiler)`, `androidx.hilt.navigation.compose`
3. Create `MyApplication : Application()` annotated with `@HiltAndroidApp`; register in `AndroidManifest.xml`
4. Annotate `MainActivity` with `@AndroidEntryPoint`
5. Convert repository class to use `@Inject constructor`
6. Extract a repository interface; add `di/AppModule.kt` with `@Binds` binding
7. Annotate each ViewModel with `@HiltViewModel @Inject constructor`; remove companion object factories
8. Replace `viewModel(factory = ...)` with `hiltViewModel()` in each Route composable
9. Remove repository parameters from `AppNavigation.kt` (Hilt now provides them)

**Cost estimate:** 2–4 hours for a 3-feature Tier 1 app. The migration is well-defined and
mechanical. This is why it is not premature to use Tier 1 initially.

### Tier 2 → Tier 3 (Adding Multi-Module)

Steps in order:

1. Create `build-logic/` with convention plugins (`AndroidLibraryConventionPlugin`,
   `AndroidFeatureConventionPlugin`, `AndroidHiltConventionPlugin`, etc.)
2. Create `core:model` module — move all data/domain classes
3. Create `core:data` module — move repositories and their interfaces
4. Create `core:database` module — move Room DAOs and entities (if using Room)
5. Create `core:testing` module — move test doubles and `TestDispatcherRule`
6. For each feature package, create `feature:name:api` (navigation key) and
   `feature:name:impl` (Screen + ViewModel + DI) modules
7. Update `settings.gradle.kts` to include all new modules
8. Update `app/build.gradle.kts` to depend on feature impl modules
9. Remove now-empty packages from `app/src/main/`

**Cost estimate:** 1–3 days per feature for a 4-feature Tier 2 app. This migration is
expensive, which is why Tier 2 is not merely a stepping stone — it is the correct permanent
tier for many apps.
