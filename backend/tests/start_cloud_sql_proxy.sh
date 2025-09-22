#!/bin/bash

# Cloud SQL Proxy v2 スタートアップスクリプト
# 使用方法: ./start_cloud_sql_proxy.sh [options]

set -e

# 設定
INSTANCE_CONNECTION_NAME="comic-ai-agent-470309:asia-northeast1:manga-db-prod"
DEFAULT_PORT=5432
PROXY_BINARY="./cloud_sql_proxy"

# カラー出力
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# ヘルプ表示
show_help() {
    echo -e "${BLUE}Cloud SQL Proxy v2 スタートアップスクリプト${NC}"
    echo ""
    echo "使用方法: $0 [オプション]"
    echo ""
    echo "オプション:"
    echo "  -p, --port PORT     プロキシのポート番号 (デフォルト: 5432)"
    echo "  -b, --background    バックグラウンドで実行"
    echo "  -d, --debug         デバッグログを有効化"
    echo "  -h, --health        ヘルスチェックを有効化"
    echo "  -t, --test          接続テストを実行"
    echo "  -s, --stop          実行中のプロキシを停止"
    echo "  --help              このヘルプを表示"
    echo ""
    echo "例:"
    echo "  $0                  フォアグラウンドで起動"
    echo "  $0 -b               バックグラウンドで起動"
    echo "  $0 -p 5433 -d       ポート5433でデバッグモードで起動"
    echo "  $0 -t               接続テストのみ実行"
    echo "  $0 -s               実行中のプロキシを停止"
}

# ログ出力関数
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# プロキシバイナリの確認
check_proxy_binary() {
    if [[ ! -f "$PROXY_BINARY" ]]; then
        log_error "Cloud SQL Proxyバイナリが見つかりません: $PROXY_BINARY"
        log_info "セットアップガイドを参照してください: backend/tests/cloud_sql_proxy_setup_guide.md"
        exit 1
    fi

    if [[ ! -x "$PROXY_BINARY" ]]; then
        log_warning "実行権限がありません。権限を設定します..."
        chmod +x "$PROXY_BINARY"
    fi
}

# バージョン確認
check_version() {
    local version=$($PROXY_BINARY --version 2>/dev/null || echo "unknown")
    log_info "Cloud SQL Proxy バージョン: $version"

    if [[ "$version" == *"v1"* ]]; then
        log_warning "v1が検出されました。v2への更新を推奨します。"
    fi
}

# Google Cloud認証確認
check_auth() {
    log_info "Google Cloud認証を確認中..."

    if ! command -v gcloud &> /dev/null; then
        log_error "Google Cloud SDKがインストールされていません"
        exit 1
    fi

    local auth_account=$(gcloud auth list --filter=status:ACTIVE --format="value(account)" 2>/dev/null | head -1)
    if [[ -z "$auth_account" ]]; then
        log_error "Google Cloud認証が必要です"
        log_info "次のコマンドを実行してください: gcloud auth application-default login"
        exit 1
    fi

    local project=$(gcloud config get-value project 2>/dev/null)
    if [[ -z "$project" ]]; then
        log_warning "プロジェクトが設定されていません"
        log_info "次のコマンドを実行してください: gcloud config set project comic-ai-agent-470309"
    fi

    log_success "認証済み: $auth_account (プロジェクト: $project)"
}

# ポート使用確認
check_port() {
    local port=$1
    local pid=$(lsof -ti :$port 2>/dev/null)

    if [[ -n "$pid" ]]; then
        local process_name=$(ps -p $pid -o comm= 2>/dev/null || echo "unknown")
        log_warning "ポート $port は既に使用されています (PID: $pid, プロセス: $process_name)"

        if [[ "$process_name" == *"cloud_sql"* ]]; then
            log_info "Cloud SQL Proxyが既に実行中です"
            return 1
        else
            log_error "別のプロセスがポートを使用しています"
            exit 1
        fi
    fi
    return 0
}

# プロキシ停止
stop_proxy() {
    log_info "Cloud SQL Proxyプロセスを検索中..."

    local pids=$(pgrep -f "cloud_sql_proxy.*$INSTANCE_CONNECTION_NAME" 2>/dev/null || true)

    if [[ -z "$pids" ]]; then
        log_info "実行中のCloud SQL Proxyが見つかりません"
        return 0
    fi

    log_info "Cloud SQL Proxyプロセスを停止中... (PID: $pids)"
    echo $pids | xargs kill

    # 停止確認
    sleep 2
    local remaining=$(pgrep -f "cloud_sql_proxy.*$INSTANCE_CONNECTION_NAME" 2>/dev/null || true)
    if [[ -n "$remaining" ]]; then
        log_warning "強制終了します..."
        echo $remaining | xargs kill -9
    fi

    log_success "Cloud SQL Proxyを停止しました"
}

# 接続テスト
test_connection() {
    local port=$1
    log_info "接続テストを実行中..."

    # PostgreSQL クライアントの確認
    if ! command -v psql &> /dev/null; then
        log_error "psqlコマンドが見つかりません。PostgreSQLクライアントをインストールしてください。"
        exit 1
    fi

    # 環境変数の確認
    if [[ -z "$PGPASSWORD" ]]; then
        export PGPASSWORD="manga_secure_password_2024"
        log_info "PGPASSWORD環境変数を設定しました"
    fi

    # 接続テスト実行
    local test_result
    test_result=$(psql -h 127.0.0.1 -p $port -U manga_user -d manga_db -c "SELECT 'Connection test successful' as result;" -t 2>/dev/null | tr -d ' \n' || echo "FAILED")

    if [[ "$test_result" == "Connectiontestsuccessful" ]]; then
        log_success "データベース接続テスト成功"

        # 追加情報取得
        local db_version=$(psql -h 127.0.0.1 -p $port -U manga_user -d manga_db -c "SELECT version();" -t 2>/dev/null | head -1 | cut -c1-50 || echo "unknown")
        local table_count=$(psql -h 127.0.0.1 -p $port -U manga_user -d manga_db -c "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public';" -t 2>/dev/null | tr -d ' \n' || echo "0")

        log_info "データベース: $db_version..."
        log_info "テーブル数: $table_count"
    else
        log_error "データベース接続テスト失敗"
        exit 1
    fi
}

# プロキシ起動
start_proxy() {
    local port=$1
    local background=$2
    local debug=$3
    local health=$4

    # コマンド構築
    local cmd="$PROXY_BINARY $INSTANCE_CONNECTION_NAME --port $port"

    if [[ "$debug" == "true" ]]; then
        cmd="$cmd --debug-logs"
        log_info "デバッグログを有効にしました"
    fi

    if [[ "$health" == "true" ]]; then
        cmd="$cmd --health-check --http-port 9090"
        log_info "ヘルスチェックを有効にしました (ポート 9090)"
    fi

    log_info "Cloud SQL Proxyを起動中..."
    log_info "コマンド: $cmd"

    if [[ "$background" == "true" ]]; then
        # バックグラウンド実行
        $cmd > /tmp/cloud_sql_proxy.log 2>&1 &
        local proxy_pid=$!

        # 起動確認
        sleep 3
        if kill -0 $proxy_pid 2>/dev/null; then
            log_success "Cloud SQL Proxyをバックグラウンドで起動しました (PID: $proxy_pid)"
            log_info "ログファイル: /tmp/cloud_sql_proxy.log"

            # 接続テスト
            test_connection $port
        else
            log_error "Cloud SQL Proxyの起動に失敗しました"
            log_info "ログを確認してください: /tmp/cloud_sql_proxy.log"
            exit 1
        fi
    else
        # フォアグラウンド実行
        log_info "Cloud SQL Proxyを起動します (Ctrl+Cで停止)"
        log_info "別ターミナルで接続テストを実行: $0 -t"
        exec $cmd
    fi
}

# メイン処理
main() {
    local port=$DEFAULT_PORT
    local background=false
    local debug=false
    local health=false
    local test_only=false
    local stop_only=false

    # 引数解析
    while [[ $# -gt 0 ]]; do
        case $1 in
            -p|--port)
                port="$2"
                shift 2
                ;;
            -b|--background)
                background=true
                shift
                ;;
            -d|--debug)
                debug=true
                shift
                ;;
            -h|--health)
                health=true
                shift
                ;;
            -t|--test)
                test_only=true
                shift
                ;;
            -s|--stop)
                stop_only=true
                shift
                ;;
            --help)
                show_help
                exit 0
                ;;
            *)
                log_error "不明なオプション: $1"
                show_help
                exit 1
                ;;
        esac
    done

    # 停止のみの場合
    if [[ "$stop_only" == "true" ]]; then
        stop_proxy
        exit 0
    fi

    # 基本チェック
    check_proxy_binary
    check_version
    check_auth

    # テストのみの場合
    if [[ "$test_only" == "true" ]]; then
        if ! check_port $port; then
            log_info "既存のプロキシに接続テストを実行します"
        else
            log_error "ポート $port でCloud SQL Proxyが実行されていません"
            log_info "先にプロキシを起動してください: $0 -b"
            exit 1
        fi
        test_connection $port
        exit 0
    fi

    # ポート使用確認
    if ! check_port $port; then
        log_error "ポート $port は既に使用されています"
        log_info "別のポートを指定するか、既存のプロセスを停止してください: $0 -s"
        exit 1
    fi

    # プロキシ起動
    start_proxy $port $background $debug $health
}

# エラートラップ
trap 'log_error "スクリプトが予期せず終了しました"' ERR

# メイン処理実行
main "$@"