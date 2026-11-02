package handlers

import "net/http"

func Greet(w http.ResponseWriter, r *http.Request) {
    name := r.URL.Query().Get("name")
    if name == "" {
        name = "stranger"
    }
    w.Header().Set("Content-Type", "text/plain")
    _, _ = w.Write([]byte("Hello, " + name + "!"))
}
