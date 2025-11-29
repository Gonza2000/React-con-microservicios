import React, { useState, useEffect } from "react";

function App() {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [loginMsg, setLoginMsg] = useState("");
  const [users, setUsers] = useState([]);

  const [appointments, setAppointments] = useState([]);
  const [patientName, setPatientName] = useState("");
  const [doctorName, setDoctorName] = useState("");
  const [date, setDate] = useState("");

  const [plans, setPlans] = useState([]);
  const [planMsg, setPlanMsg] = useState("");

  const handleRegister = async () => {
    try {
      const res = await fetch("http://host.docker.internal:8001/register", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ username, password }),
      });
      const data = await res.json();
      setLoginMsg(data.message || data.detail);
      fetchUsers(); // actualizar lista
    } catch (e) {
      setLoginMsg("Error Python");
    }
  };

  const handleLogin = async () => {
    try {
      const res = await fetch("http://host.docker.internal:8001/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ username, password }),
      });
      const data = await res.json();
      setLoginMsg(data.message || data.detail);
    } catch (e) {
      setLoginMsg("Error Python");
    }
  };

  const fetchUsers = async () => {
    try {
      const res = await fetch("http://host.docker.internal:8001/users");
      const data = await res.json();
      setUsers(data);
    } catch (e) {
      console.error("Error fetching users");
    }
  };


  const fetchAppointments = async () => {
    try {
      const res = await fetch("http://localhost:8002/appointments");
      const data = await res.json();
      setAppointments(data);
    } catch (e) {
      console.error("Java Error");
    }
  };
  const createAppointment = async () => {
    await fetch("http://localhost:8002/appointments", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ patientName, doctorName, date }),
    });
    fetchAppointments();
  };
  const deleteAppointment = async (id) => {
    await fetch(`http://localhost:8002/appointments/${id}`, { method: "DELETE" });
    fetchAppointments();
  };


  const fetchPlans = async () => {
    try {
      const res = await fetch("http://localhost:8003/plans");
      const data = await res.json();
      setPlans(data || []);
    } catch (e) {
      console.error("Go Error");
    }
  };
  const buyPlan = async (id) => {
    const res = await fetch("http://localhost:8003/buy", { method: "POST" });
    const data = await res.json();
    setPlanMsg(`Plan ${id}: ${data.message}`);
  };

  useEffect(() => {
    fetchAppointments();
    fetchPlans();
    fetchUsers();
  }, []);


  return (
    <div style={{ padding: "20px", fontFamily: "Arial, sans-serif" }}>
      <h1>🌐 Sistema de Microservicios</h1>

    
      <div style={{ border: "1px solid #ccc", padding: "15px", marginBottom: "20px", borderRadius: "8px" }}>
        <h2 style={{ color: "#3776ab" }}>Microservicio 1: Python (Login) :8001</h2>
        <input placeholder="Usuario" onChange={(e) => setUsername(e.target.value)} style={{ marginRight: "10px" }} />
        <input type="password" placeholder="Contraseña" onChange={(e) => setPassword(e.target.value)} style={{ marginRight: "10px" }} />
        <button onClick={handleRegister}>Registrar</button>{" "}
        <button onClick={handleLogin}>Login</button>
        <p>Status: <strong>{loginMsg}</strong></p>

        <h3>Usuarios registrados:</h3>
        <ul>
          {users.map((u) => (
            <li key={u.id}>{u.id} - {u.username}</li>
          ))}
        </ul>
      </div>

  
      <div style={{ border: "1px solid #ccc", padding: "15px", marginBottom: "20px", borderRadius: "8px" }}>
        <h2 style={{ color: "#f89820" }}>Microservicio 2: Java (Citas) :8002</h2>
        <input placeholder="Paciente" onChange={(e) => setPatientName(e.target.value)} style={{ marginRight: "10px" }} />
        <input placeholder="Doctor" onChange={(e) => setDoctorName(e.target.value)} style={{ marginRight: "10px" }} />
        <input type="date" onChange={(e) => setDate(e.target.value)} style={{ marginRight: "10px" }} />
        <button onClick={createAppointment}>Agendar</button>
        <ul style={{ marginTop: "10px" }}>
          {appointments.map((a) => (
            <li key={a.id} style={{ marginBottom: "5px" }}>
              {a.date}: {a.patientName} con {a.doctorName}
              <button onClick={() => deleteAppointment(a.id)} style={{ marginLeft: "10px", color: "red", cursor: "pointer" }}>Eliminar</button>
            </li>
          ))}
        </ul>
      </div>

   
      <div style={{ border: "1px solid #ccc", padding: "15px", borderRadius: "8px" }}>
        <h2 style={{ color: "#00add8" }}>Microservicio 3: Go (Planes) :8003</h2>
        <div style={{ display: "flex", gap: "20px" }}>
          {plans.map((p) => (
            <div key={p.id} style={{ border: "1px solid #eee", padding: "10px", borderRadius: "5px", background: "#f9f9f9" }}>
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
