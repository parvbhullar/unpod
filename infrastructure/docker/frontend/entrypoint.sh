#!/bin/sh
set -e

# =============================================================================
# Unpod Web Frontend — Runtime Environment Injection
# =============================================================================
# Replaces build-time placeholder strings in the pre-built JS files with
# actual environment variable values. This keeps the Docker image reusable
# across environments (dev, staging, prod) without rebuilding.
# =============================================================================

replace_env() {
  local placeholder="$1" value="$2"
  if [ -n "$value" ]; then
    find /app/apps/web/.next -name '*.js' -exec grep -l "$placeholder" {} + 2>/dev/null | \
      xargs -r sed -i "s|$placeholder|$value|g"
  fi
}

replace_env "__UNPOD_APP_TYPE__"            "${appType:-social}"
replace_env "__UNPOD_API_URL__"             "${apiUrl:-http://localhost:8000/api/v1/}"
replace_env "__UNPOD_SERVER_API_URL__"      "${serverApiUrl:-http://backend-core:8000/api/v1/}"
replace_env "__UNPOD_CHAT_API_URL__"        "${chatApiUrl:-ws://localhost:8000/ws/v1/}"
replace_env "__UNPOD_SITE_URL__"            "${siteUrl:-http://localhost:3000}"
replace_env "__UNPOD_PRODUCT_ID__"          "${productId:-unpod.ai}"
replace_env "__UNPOD_IS_DEV_MODE__"         "${isDevMode:-yes}"
replace_env "__UNPOD_CURRENCY__"            "${currency:-INR}"
replace_env "__UNPOD_NO_INDEX__"            "${noIndex:-yes}"
replace_env "__UNPOD_NO_FOLLOW__"           "${noFollow:-yes}"
replace_env "__UNPOD_PAYMENT_GATEWAY_KEY__" "${paymentGatewayKey:-}"
replace_env "__UNPOD_ENABLE_CHECKSUM__"     "${ENABLE_CHECKSUM:-false}"

echo "Environment variables injected, starting server..."
exec "$@"
