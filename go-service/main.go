package main

import (
	"database/sql"
	"encoding/json"
	"log"
	"net/http"
	_ "github.com/mattn/go-sqlite3"
    "github.com/rs/cors"
)

var db *sql.DB

type Plan struct {
	ID    int    `json:"id"`
	Name  string `json:"name"`
	Price int    `json:"price"`
}

func initDB() {
	var err error
	db, err = sql.Open("sqlite3", "./plans.db")
	if err != nil { log.Fatal(err) }
	statement, _ := db.Prepare("CREATE TABLE IF NOT EXISTS plans (id INTEGER PRIMARY KEY, name TEXT, price INTEGER)")
	statement.Exec()
    db.Exec("INSERT OR IGNORE INTO plans (id, name, price) VALUES (1, 'Basic', 10)")
    db.Exec("INSERT OR IGNORE INTO plans (id, name, price) VALUES (2, 'Premium', 50)")
}

func getPlans(w http.ResponseWriter, r *http.Request) {
	rows, _ := db.Query("SELECT id, name, price FROM plans")
	var plans []Plan
	for rows.Next() {
		var p Plan
		rows.Scan(&p.ID, &p.Name, &p.Price)
		plans = append(plans, p)
	}
    if plans == nil { plans = []Plan{} }
	json.NewEncoder(w).Encode(plans)
}

func buyPlan(w http.ResponseWriter, r *http.Request) {
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusOK)
	w.Write([]byte(`{"message": "Plan purchased successfully"}`))
}

func main() {
	initDB()
	mux := http.NewServeMux()
	mux.HandleFunc("/plans", getPlans)
	mux.HandleFunc("/buy", buyPlan)
    c := cors.New(cors.Options{
        AllowedOrigins: []string{"*"},
        AllowedMethods: []string{"GET", "POST", "OPTIONS"},
        AllowedHeaders: []string{"*"},
    })
	log.Println("Go service running on 8003")
	http.ListenAndServe(":8003", c.Handler(mux))
}
