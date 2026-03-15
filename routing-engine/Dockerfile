# Multi-stage Rust build for routing-engine
FROM rust:1.85-slim-bookworm AS builder
WORKDIR /app
COPY Cargo.toml Cargo.lock* ./
# Cache deps
RUN mkdir src && echo "fn main(){}" > src/main.rs && cargo build --release && rm -rf src
COPY src ./src
RUN touch src/main.rs && cargo build --release

FROM gcr.io/distroless/cc-debian12 AS runtime

COPY --from=builder /app/target/release/routing-engine /usr/local/bin/routing-engine
EXPOSE 3000
ENV RUST_LOG=routing_engine=info
CMD ["routing-engine"]
