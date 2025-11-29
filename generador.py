import os

# Definición de la estructura y contenido de los archivos
project_structure = {
    # --- ROOT ---
    "docker-compose.yml": """version: '3.8'

services:
  users-service:
    build: ./users
    ports:
      - "8001:8001"
    container_name: python_users_ms

  java-service:
    build: ./java-service
    ports:
      - "8002:8002"
    container_name: java_appointments_ms

  go-service:
    build: ./go-service
    ports:
      - "8003:8003"
    container_name: go_plans_ms

  frontend:
    build: ./frontend
    ports:
      - "3000:3000"
    volumes:
      - ./frontend/src:/app/src
    stdin_open: true
    tty: true
    depends_on:
      - users-service
      - java-service
      - go-service
""",

    # --- PYTHON SERVICE ---
    "users/requirements.txt": """fastapi
uvicorn
sqlmodel
""",
    "users/Dockerfile": """FROM python:3.9-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY ./app /app
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8001"]
""",
    "users/app/main.py": """from fastapi import FastAPI, HTTPException
from sqlmodel import SQLModel, Field, create_engine, Session, select
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware

sqlite_file_name = "users.db"
sqlite_url = f"sqlite:///{sqlite_file_name}"
engine = create_engine(sqlite_url)

class User(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    username: str
    password: str

def create_db_and_tables():
    SQLModel.metadata.create_all(engine)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def on_startup():
    create_db_and_tables()

class UserLogin(BaseModel):
    username: str
    password: str

@app.post("/register")
def register(user: UserLogin):
    with Session(engine) as session:
        existing_user = session.exec(select(User).where(User.username == user.username)).first()
        if existing_user:
            raise HTTPException(status_code=400, detail="Username already exists")
        new_user = User(username=user.username, password=user.password)
        session.add(new_user)
        session.commit()
        return {"message": "User registered successfully"}

@app.post("/login")
def login(user: UserLogin):
    with Session(engine) as session:
        statement = select(User).where(User.username == user.username).where(User.password == user.password)
        result = session.exec(statement).first()
        if not result:
            raise HTTPException(status_code=401, detail="Invalid credentials")
        return {"message": "Login successful", "user_id": result.id}
""",

    # --- JAVA SERVICE ---
    "java-service/Dockerfile": """FROM maven:3.8.5-openjdk-17 AS build
WORKDIR /app
COPY pom.xml .
COPY src ./src
RUN mvn clean package -DskipTests

FROM openjdk:17-jdk-slim
WORKDIR /app
COPY --from=build /app/target/*.jar app.jar
EXPOSE 8002
ENTRYPOINT ["java", "-jar", "app.jar"]
""",
    "java-service/pom.xml": """<?xml version="1.0" encoding="UTF-8"?>
<project xmlns="http://maven.apache.org/POM/4.0.0"
         xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
         xsi:schemaLocation="http://maven.apache.org/POM/4.0.0 http://maven.apache.org/xsd/maven-4.0.0.xsd">
    <modelVersion>4.0.0</modelVersion>
    <groupId>com.example</groupId>
    <artifactId>medical-appointments</artifactId>
    <version>0.0.1-SNAPSHOT</version>
    <parent>
        <groupId>org.springframework.boot</groupId>
        <artifactId>spring-boot-starter-parent</artifactId>
        <version>3.1.5</version>
    </parent>
    <dependencies>
        <dependency>
            <groupId>org.springframework.boot</groupId>
            <artifactId>spring-boot-starter-web</artifactId>
        </dependency>
        <dependency>
            <groupId>org.springframework.boot</groupId>
            <artifactId>spring-boot-starter-data-jpa</artifactId>
        </dependency>
        <dependency>
            <groupId>org.xerial</groupId>
            <artifactId>sqlite-jdbc</artifactId>
        </dependency>
        <dependency>
            <groupId>org.hibernate.orm</groupId>
            <artifactId>hibernate-community-dialects</artifactId>
        </dependency>
    </dependencies>
    <build>
        <plugins>
            <plugin>
                <groupId>org.springframework.boot</groupId>
                <artifactId>spring-boot-maven-plugin</artifactId>
            </plugin>
        </plugins>
    </build>
</project>
""",
    "java-service/src/main/resources/application.properties": """server.port=8002
spring.datasource.url=jdbc:sqlite:appointments.db
spring.datasource.driver-class-name=org.sqlite.JDBC
spring.jpa.database-platform=org.hibernate.community.dialect.SQLiteDialect
spring.jpa.hibernate.ddl-auto=update
""",
    "java-service/src/main/java/com/example/medical/MedicalApplication.java": """package com.example.medical;

import jakarta.persistence.*;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.servlet.config.annotation.CorsRegistry;
import org.springframework.web.servlet.config.annotation.WebMvcConfigurer;
import org.springframework.context.annotation.Bean;
import java.util.List;

@SpringBootApplication
public class MedicalApplication {
    public static void main(String[] args) {
        SpringApplication.run(MedicalApplication.class, args);
    }

    @Bean
    public WebMvcConfigurer corsConfigurer() {
        return new WebMvcConfigurer() {
            @Override
            public void addCorsMappings(CorsRegistry registry) {
                registry.addMapping("/**").allowedOrigins("*").allowedMethods("*");
            }
        };
    }
}

@Entity
class Appointment {
    @Id @GeneratedValue(strategy = GenerationType.IDENTITY)
    public Long id;
    public String patientName;
    public String doctorName;
    public String date;
}

interface AppointmentRepository extends JpaRepository<Appointment, Long> {}

@RestController
@RequestMapping("/appointments")
class AppointmentController {
    private final AppointmentRepository repository;

    public AppointmentController(AppointmentRepository repository) {
        this.repository = repository;
    }

    @PostMapping
    public Appointment create(@RequestBody Appointment appointment) {
        return repository.save(appointment);
    }

    @GetMapping
    public List<Appointment> getAll() {
        return repository.findAll();
    }

    @DeleteMapping("/{id}")
    public void delete(@PathVariable Long id) {
        repository.deleteById(id);
    }
}
""",

    # --- GO SERVICE ---
    "go-service/Dockerfile": """FROM golang:1.20-alpine
RUN apk add --no-cache build-base
WORKDIR /app
COPY go.mod ./
RUN go mod download
RUN go get github.com/mattn/go-sqlite3
RUN go get github.com/rs/cors
COPY . .
RUN go build -o main .
CMD ["./main"]
""",
    "go-service/go.mod": """module go-service
go 1.20
require (
	github.com/mattn/go-sqlite3 v1.14.17
    github.com/rs/cors v1.10.1
)
""",
    "go-service/main.go": """package main

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
""",

    # --- FRONTEND (REACT) ---
    "frontend/Dockerfile": """FROM node:18-alpine
WORKDIR /app
COPY package.json .
RUN npm install
COPY . .
EXPOSE 3000
CMD ["npm", "start"]
""",
    "frontend/package.json": """{
  "name": "frontend",
  "version": "0.1.0",
  "private": true,
  "dependencies": {
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "react-scripts": "5.0.1",
    "web-vitals": "^2.1.4"
  },
  "scripts": {
    "start": "react-scripts start",
    "build": "react-scripts build",
    "test": "react-scripts test",
    "eject": "react-scripts eject"
  },
  "eslintConfig": {
    "extends": [
      "react-app",
      "react-app/jest"
    ]
  },
  "browserslist": {
    "production": [
      ">0.2%",
      "not dead",
      "not op_mini all"
    ],
    "development": [
      "last 1 chrome version",
      "last 1 firefox version",
      "last 1 safari version"
    ]
  }
}
""",
    "frontend/public/index.html": """<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>Microservices App</title>
  </head>
  <body>
    <noscript>You need to enable JavaScript to run this app.</noscript>
    <div id="root"></div>
  </body>
</html>
""",
    "frontend/src/index.js": """import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App';

const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);
""",
    "frontend/src/App.js": """import React, { useState, useEffect } from 'react';

function App() {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [loginMsg, setLoginMsg] = useState('');

  const [appointments, setAppointments] = useState([]);
  const [patientName, setPatientName] = useState('');
  const [doctorName, setDoctorName] = useState('');
  const [date, setDate] = useState('');

  const [plans, setPlans] = useState([]);
  const [planMsg, setPlanMsg] = useState('');

  // PYTHON
  const handleRegister = async () => {
    try {
      const res = await fetch('http://localhost:8001/register', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, password })
      });
      const data = await res.json();
      setLoginMsg(data.message || data.detail);
    } catch (e) { setLoginMsg('Error Python'); }
  };

  const handleLogin = async () => {
    try {
      const res = await fetch('http://localhost:8001/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, password })
      });
      const data = await res.json();
      setLoginMsg(data.message || data.detail);
    } catch (e) { setLoginMsg('Error Python'); }
  };

  // JAVA
  const fetchAppointments = async () => {
    try {
      const res = await fetch('http://localhost:8002/appointments');
      const data = await res.json();
      setAppointments(data);
    } catch (e) { console.error("Java Error"); }
  };
  const createAppointment = async () => {
    await fetch('http://localhost:8002/appointments', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ patientName, doctorName, date })
    });
    fetchAppointments();
  };
  const deleteAppointment = async (id) => {
    await fetch(`http://localhost:8002/appointments/${id}`, { method: 'DELETE' });
    fetchAppointments();
  };

  // GO
  const fetchPlans = async () => {
    try {
      const res = await fetch('http://localhost:8003/plans');
      const data = await res.json();
      setPlans(data || []);
    } catch (e) { console.error("Go Error"); }
  };
  const buyPlan = async (id) => {
    const res = await fetch('http://localhost:8003/buy', { method: 'POST' });
    const data = await res.json();
    setPlanMsg(`Plan ${id}: ${data.message}`);
  };

  useEffect(() => {
    fetchAppointments();
    fetchPlans();
  }, []);

  return (
    <div style={{ padding: '20px', fontFamily: 'sans-serif' }}>
      <h1>Sistema de Microservicios</h1>
      
      <div style={{ border: '1px solid #ccc', padding: '15px', marginBottom: '20px', borderRadius: '8px' }}>
        <h2 style={{color: '#3776ab'}}>Microservicio 1: Python (Login) :8001</h2>
        <input placeholder="Usuario" onChange={e => setUsername(e.target.value)} style={{marginRight:'10px'}}/>
        <input type="password" placeholder="Contraseña" onChange={e => setPassword(e.target.value)} style={{marginRight:'10px'}}/>
        <button onClick={handleRegister}>Registrar</button> <button onClick={handleLogin}>Login</button>
        <p>Status: <strong>{loginMsg}</strong></p>
      </div>

      <div style={{ border: '1px solid #ccc', padding: '15px', marginBottom: '20px', borderRadius: '8px' }}>
        <h2 style={{color: '#f89820'}}>Microservicio 2: Java (Citas) :8002</h2>
        <input placeholder="Paciente" onChange={e => setPatientName(e.target.value)} style={{marginRight:'10px'}}/>
        <input placeholder="Doctor" onChange={e => setDoctorName(e.target.value)} style={{marginRight:'10px'}}/>
        <input type="date" onChange={e => setDate(e.target.value)} style={{marginRight:'10px'}}/>
        <button onClick={createAppointment}>Agendar</button>
        <ul style={{marginTop:'10px'}}>
          {appointments.map(a => (
            <li key={a.id} style={{marginBottom:'5px'}}>
              {a.date}: {a.patientName} con {a.doctorName}
              <button onClick={() => deleteAppointment(a.id)} style={{marginLeft: '10px', color:'red', cursor:'pointer'}}>Eliminar</button>
            </li>
          ))}
        </ul>
      </div>

      <div style={{ border: '1px solid #ccc', padding: '15px', borderRadius: '8px' }}>
        <h2 style={{color: '#00add8'}}>Microservicio 3: Go (Planes) :8003</h2>
        <div style={{display:'flex', gap:'20px'}}>
          {plans.map(p => (
            <div key={p.id} style={{border:'1px solid #eee', padding:'10px', borderRadius:'5px', background:'#f9f9f9'}}>
              <h3>{p.name}</h3>
              <p>Precio: ${p.price}</p>
              <button onClick={() => buyPlan(p.id)}>Comprar</button>
            </div>
          ))}
        </div>
        <p>Resultado: <strong>{planMsg}</strong></p>
      </div>
    </div>
  );
}
export default App;
"""
}

def create_files():
    base_dir = os.getcwd()
    print(f"Generando proyecto en: {base_dir}")
    
    for file_path, content in project_structure.items():
        # Construir ruta completa
        full_path = os.path.join(base_dir, file_path)
        # Crear directorios si no existen
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        
        # Escribir archivo (usando utf-8 para caracteres especiales)
        with open(full_path, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"Creado: {file_path}")

if __name__ == "__main__":
    create_files()
    print("\n¡Todo listo!")
    print("Pasos siguientes:")
    print("1. Borra este script si lo deseas.")
    print("2. Ejecuta: docker-compose up --build")