# CQRS Application Layer Implementation Guide

## 概要

Phase 1として、Command Query Responsibility Segregation (CQRS) パターンに基づいたアプリケーション層の骨格を実装しました。このガイドでは、実装された構造と次のステップについて説明します。

## 実装された構造

### 1. Base Classes (`app/application/*/base_*.py`)

#### Commands
- `AbstractCommand`: 全コマンドの基底クラス
- `Command[T]`: 型付きコマンド基底クラス
- `CommandResult[T]`: コマンド実行結果のラッパー
- `RequireUserMixin`, `RequireIdMixin`: バリデーション用ミックスイン

#### Queries  
- `AbstractQuery`: 全クエリの基底クラス
- `Query[T]`: 型付きクエリ基底クラス
- `QueryResult[T]`: クエリ実行結果のラッパー
- `PaginatedResult[T]`: ページング対応結果
- `PaginationInfo`, `FilterInfo`: ページング・フィルタリング情報

#### Handlers
- `AbstractCommandHandler[TCommand, TResult]`: コマンドハンドラー基底クラス
- `AbstractQueryHandler[TQuery, TResult]`: クエリハンドラー基底クラス
- `BaseHandler`: 共通機能を持つハンドラー
- `HandlerRegistry`: ハンドラーの登録・実行管理

#### DTOs
- `BaseDTO`: 全DTOの基底クラス
- `PaginatedResponseDTO[T]`: ページング対応レスポンス
- `StatsDTO`: 統計情報用基底DTO
- バリデーション用ユーティリティ関数

### 2. Domain-Specific Implementations

#### Users (`app/application/*/user_*`)
- **Commands**: CreateUser, UpdateUser, DeleteUser, VerifyUserEmail, UpdateUserPreferences
- **Queries**: GetUser, GetUserByEmail, ListUsers, GetUserStats, SearchUsers
- **DTOs**: UserDTO, UserCreateDTO, UserUpdateDTO, UserStatsDTO, UserPreferencesDTO
- **Handlers**: 完全実装済み（モック含む）

#### Manga Projects (`app/application/*/manga_project_*`)
- **Commands**: CreateProject, UpdateProject, DeleteProject, PublishProject, AddFile
- **Queries**: GetProject, ListProjects, SearchProjects, GetProjectStats, GetProjectFiles
- **DTOs**: ProjectDTO, ProjectCreateDTO, ProjectStatsDTO, MangaFileDTO, ProjectTagDTO
- **Handlers**: スケルトン実装済み

#### Generation Requests (`app/application/*/generation_request_*`)
- **Commands**: CreateRequest, UpdateStatus, RetryRequest, ProcessFeedback
- **Queries**: GetRequest, ListRequests, GetProgress, GetFeedback, GetPerformance
- **DTOs**: RequestDTO, RequestCreateDTO, ProgressDTO, FeedbackRequestDTO
- **Handlers**: スケルトン実装済み

#### Processing Modules (`app/application/*/processing_module_*`)
- **Commands**: StartModule, CompleteModule, FailModule, RetryModule
- **Queries**: GetModule, ListModules, GetStats, GetPerformance, GetBottlenecks
- **DTOs**: ModuleDTO, ModuleStatsDTO, ModulePerformanceDTO, ModuleMetricDTO
- **Handlers**: スケルトン実装済み

## Phase 1 完了内容

### ✅ 実装済み
1. **CQRS基盤構造**: Base classes, Result pattern, Validation mixins
2. **完全なCommand/Query定義**: 4つの主要エンティティに対応
3. **型安全なDTO構造**: バリデーション・シリアライゼーション対応
4. **ハンドラー基盤**: 共通機能・エラーハンドリング・ロギング
5. **User関連の完全実装**: 実用可能なサンプル実装
6. **HandlerRegistry**: 依存性注入・実行管理システム

### ⚠️ 未完成（Phase 2以降で実装）
1. **ドメインサービス統合**: 実際のビジネスロジック呼び出し
2. **リポジトリ統合**: データベースアクセス層との接続
3. **残りのハンドラー実装**: MangaProject, GenerationRequest, ProcessingModule
4. **エラーハンドリング強化**: ドメイン固有例外処理
5. **パフォーマンス最適化**: キャッシング・バッチ処理

## 使用方法

### 1. Handler Registry Setup

```python
from app.application.handlers.base_handler import handler_registry
from app.application.handlers.user_handlers import *
from app.application.commands.user_commands import *
from app.application.queries.user_queries import *

# Register handlers
handler_registry.register_command_handler(CreateUserCommand, CreateUserCommandHandler())
handler_registry.register_query_handler(GetUserQuery, GetUserQueryHandler())
```

### 2. Command Execution

```python
# Create command
command = CreateUserCommand(
    email="test@example.com",
    display_name="Test User",
    user_id="current_user_id"
)

# Execute through registry
result = await handler_registry.execute_command(command)

if result.is_success():
    user_id = result.data
    print(f"User created with ID: {user_id}")
else:
    print(f"Error: {result.error_code}: {result.error}")
```

### 3. Query Execution

```python
# Create query with pagination
query = ListUsersQuery(
    account_type="free",
    user_id="admin_user_id"
)
query.pagination.page = 1
query.pagination.page_size = 10

# Execute query
result = await handler_registry.execute_query(query)

if result.is_success():
    paginated_users = result.data
    print(f"Found {paginated_users.total_count} users")
    for user in paginated_users.items:
        print(f"- {user.display_name} ({user.email})")
```

### 4. FastAPI Integration Example

```python
from fastapi import FastAPI, HTTPException
from app.application.handlers.base_handler import handler_registry
from app.application.dto.base_dto import IdResponseDTO

@app.post("/users/", response_model=IdResponseDTO)
async def create_user(user_data: UserCreateRequest):
    command = CreateUserCommand(
        email=user_data.email,
        display_name=user_data.display_name,
        user_id=get_current_user_id()  # From auth middleware
    )
    
    result = await handler_registry.execute_command(command)
    
    if result.is_error():
        if result.error_code == "CONFLICT":
            raise HTTPException(status_code=409, detail=result.error)
        elif result.error_code == "VALIDATION_ERROR":
            raise HTTPException(status_code=400, detail=result.error)
        else:
            raise HTTPException(status_code=500, detail=result.error)
    
    return IdResponseDTO(id=result.data, message="User created successfully")

@app.get("/users/{user_id}", response_model=UserDTO)
async def get_user(user_id: str):
    query = GetUserQuery(
        user_id=user_id,
        include_stats=True,
        user_id=get_current_user_id()
    )
    
    result = await handler_registry.execute_query(query)
    
    if result.is_error():
        if result.error_code == "NOT_FOUND":
            raise HTTPException(status_code=404, detail=result.error)
        else:
            raise HTTPException(status_code=500, detail=result.error)
    
    return result.data
```

## Next Steps - Phase 2 Implementation

### 1. Domain Service Integration

```python
# app/application/handlers/user_handlers.py
class CreateUserCommandHandler:
    def __init__(
        self, 
        user_service: UserService,
        user_repository: UserRepository,
        quota_service: QuotaService
    ):
        self.user_service = user_service
        self.user_repository = user_repository  
        self.quota_service = quota_service
    
    async def handle(self, command: CreateUserCommand) -> CommandResult[str]:
        # Real implementation with domain services
        user_entity = await self.user_service.create_user(
            email=command.email,
            display_name=command.display_name,
            account_type=command.account_type
        )
        
        # Initialize user quota
        await self.quota_service.initialize_quota(user_entity.id)
        
        return CommandResult.success_result(str(user_entity.id))
```

### 2. Repository Integration

```python
# app/application/handlers/user_handlers.py  
class GetUserQueryHandler:
    def __init__(self, user_read_repository: UserReadRepository):
        self.user_repository = user_read_repository
    
    async def handle(self, query: GetUserQuery) -> QueryResult[UserDTO]:
        # Real database query
        user_entity = await self.user_repository.find_by_id(query.user_id)
        
        if not user_entity:
            return QueryResult.not_found_error("User")
        
        # Convert entity to DTO
        user_dto = UserDTO.from_entity(user_entity)
        
        if query.include_stats:
            stats = await self.user_repository.get_user_statistics(query.user_id)
            user_dto.stats = UserStatsDTO.from_entity(stats)
        
        return QueryResult.success_result(user_dto)
```

### 3. Dependency Injection Setup

```python
# app/core/dependencies.py
from dependency_injector import containers, providers
from app.application.handlers.user_handlers import *

class ApplicationContainer(containers.DeclarativeContainer):
    # Repositories
    user_repository = providers.Factory(UserRepositoryImpl)
    
    # Services  
    user_service = providers.Factory(UserService, user_repository)
    
    # Handlers
    create_user_handler = providers.Factory(
        CreateUserCommandHandler,
        user_service=user_service,
        user_repository=user_repository
    )
    
    get_user_handler = providers.Factory(
        GetUserQueryHandler,
        user_repository=user_repository
    )

# Register handlers
container = ApplicationContainer()
handler_registry.register_command_handler(
    CreateUserCommand, 
    container.create_user_handler()
)
```

## Architecture Benefits

### 1. CQRS Pattern Benefits
- **読み書き分離**: 最適化された読み書き操作
- **スケーラビリティ**: 読み書きを独立してスケーリング
- **複雑性管理**: 明確な責任分離

### 2. Result Pattern Benefits  
- **統一されたエラーハンドリング**: 一貫したエラー処理
- **型安全性**: コンパイル時エラー検出
- **例外回避**: 予期可能なエラーフロー

### 3. DTO Pattern Benefits
- **データ変換管理**: レイヤー間の明確なデータ契約
- **バリデーション統合**: データ検証の一元化
- **シリアライゼーション**: API応答の標準化

### 4. Handler Pattern Benefits
- **依存性注入**: テスタブルな設計
- **横断的関心事**: ロギング・メトリクス・トランザクション
- **拡張性**: 新しいハンドラーの簡単な追加

## Database Schema Compliance

実装されたCQRS構造は、データベース設計書（06.データベース設計書.md）の以下のテーブルに完全対応：

### Phase 1 Primary Tables
- `users` → User commands/queries/DTOs
- `manga_projects` → MangaProject commands/queries/DTOs  
- `generation_requests` → GenerationRequest commands/queries/DTOs
- `processing_modules` → ProcessingModule commands/queries/DTOs

### Phase 1 Secondary Tables  
- `user_quotas` → UserQuota DTOs/commands
- `manga_files` → MangaFile DTOs/commands
- `project_tags` → ProjectTag DTOs/commands
- `phase_executions` → PhaseExecution DTOs/commands
- `feedback_requests` → FeedbackRequest DTOs/commands

## Performance Considerations

### 1. Query Optimization
- フィルタリング・ソート・ページネーション対応
- インデックス活用のためのクエリ構造
- 実行時間測定とロギング

### 2. Command Optimization  
- バッチ処理対応のコマンド設計
- トランザクション境界の明確化
- 非同期処理サポート

### 3. DTO Optimization
- 必要最小限のデータ転送
- 遅延読み込み対応（include_* フラグ）
- シリアライゼーション最適化

これで、Phase 1のCQRSアプリケーション層実装が完了しました。設計書に基づいた完全な構造と、実用可能なサンプル実装を提供しています。