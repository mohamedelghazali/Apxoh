package main

import (
    "log"
    "net/http"

    "github.com/mohamedelghazali/apxoh-example-api/handlers"
)

func main() {
    mux := http.NewServeMux()
    mux.HandleFunc("/health", handlers.Health)
    mux.HandleFunc("/greet", handlers.Greet)

    log.Println("listening on :8080")
    if err := http.ListenAndServe(":8080", mux); err != nil {
        log.Fatal(err)
    }
}
