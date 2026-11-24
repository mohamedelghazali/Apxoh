package handlers

import (
    "encoding/json"
    "net/http/httptest"
    "testing"
)

func TestHealth(t *testing.T) {
    req := httptest.NewRequest("GET", "/health", nil)
    w := httptest.NewRecorder()
    Health(w, req)

    if w.Code != 200 {
        t.Fatalf("expected 200, got %d", w.Code)
    }

    var body map[string]string
    if err := json.Unmarshal(w.Body.Bytes(), &body); err != nil {
        t.Fatal(err)
    }
    if body["status"] != "ok" {
        t.Errorf("expected status=ok, got %s", body["status"])
    }
}
