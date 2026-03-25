FROM nginx:stable-bookworm-slim

WORKDIR /usr/share/nginx/html
COPY index.html .

# Add entrypoint to inject environment variables into index.html
RUN echo '#!/bin/sh\n\
if [ -n "$ROUTING_ENGINE_URL" ]; then\n\
  sed -i "s|http://localhost:3000|$ROUTING_ENGINE_URL|g" index.html\n\
fi\n\
exec nginx -g "daemon off;"' > /docker-entrypoint.d/40-inject-env.sh && \
chmod +x /docker-entrypoint.d/40-inject-env.sh

EXPOSE 80
