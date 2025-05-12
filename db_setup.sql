-- Crear la base de datos
CREATE DATABASE IF NOT EXISTS camilo;
USE camilo;

-- Eliminar tablas si existen (en caso de querer reiniciar)
SET FOREIGN_KEY_CHECKS = 0;
DROP TABLE IF EXISTS auth_user_groups;
DROP TABLE IF EXISTS auth_user_user_permissions;
DROP TABLE IF EXISTS auth_group_permissions;
DROP TABLE IF EXISTS django_admin_log;
DROP TABLE IF EXISTS auth_permission;
DROP TABLE IF EXISTS auth_group;
DROP TABLE IF EXISTS django_content_type;
DROP TABLE IF EXISTS django_session;
DROP TABLE IF EXISTS django_migrations;
DROP TABLE IF EXISTS tickets;
DROP TABLE IF EXISTS ticket_types;
DROP TABLE IF EXISTS events;
DROP TABLE IF EXISTS user_profiles;
DROP TABLE IF EXISTS auth_user;
SET FOREIGN_KEY_CHECKS = 1;

-- Crear tabla de usuarios (Esta será gestionada por Django, pero la incluimos por completitud)
CREATE TABLE IF NOT EXISTS auth_user (
    id INT AUTO_INCREMENT PRIMARY KEY,
    password VARCHAR(128) NOT NULL,
    last_login DATETIME DEFAULT NULL,
    is_superuser BOOLEAN NOT NULL DEFAULT FALSE,
    username VARCHAR(150) UNIQUE NOT NULL,
    first_name VARCHAR(150) NOT NULL,
    last_name VARCHAR(150) NOT NULL,
    email VARCHAR(254) NOT NULL,
    is_staff BOOLEAN NOT NULL DEFAULT FALSE,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    date_joined DATETIME NOT NULL
);

-- Tabla de perfiles de usuario
CREATE TABLE IF NOT EXISTS user_profiles (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    phone VARCHAR(20),
    address VARCHAR(255),
    FOREIGN KEY (user_id) REFERENCES auth_user(id) ON DELETE CASCADE
);

-- Tabla de eventos
CREATE TABLE IF NOT EXISTS events (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    event_date DATETIME NOT NULL,
    location VARCHAR(255) NOT NULL,
    capacity INT NOT NULL,
    image VARCHAR(255),
    created_at DATETIME NOT NULL,
    updated_at DATETIME NOT NULL
);

-- Tabla de tipos de entradas
CREATE TABLE IF NOT EXISTS ticket_types (
    id INT AUTO_INCREMENT PRIMARY KEY,
    event_id INT NOT NULL,
    name VARCHAR(255) NOT NULL,
    price DECIMAL(10, 2) NOT NULL,
    available_quantity INT NOT NULL,
    created_at DATETIME NOT NULL,
    updated_at DATETIME NOT NULL,
    FOREIGN KEY (event_id) REFERENCES events(id) ON DELETE CASCADE
);

-- Tabla de entradas
CREATE TABLE IF NOT EXISTS tickets (
    id INT AUTO_INCREMENT PRIMARY KEY,
    ticket_type_id INT NOT NULL,
    user_id INT NOT NULL,
    purchase_date DATETIME NOT NULL,
    ticket_code VARCHAR(255) UNIQUE NOT NULL,
    is_used BOOLEAN DEFAULT FALSE,
    FOREIGN KEY (ticket_type_id) REFERENCES ticket_types(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES auth_user(id) ON DELETE CASCADE
);

-- Insertar datos de ejemplo (esto lo hará Django automáticamente)
-- Aquí se pueden agregar inserts para datos iniciales si se desea

-- Crear un usuario administrador (esto se puede hacer con Django createsuperuser)
INSERT INTO auth_user (
    password, 
    is_superuser, 
    username, 
    first_name, 
    last_name, 
    email, 
    is_staff, 
    is_active, 
    date_joined
) VALUES (
    -- Contraseña: admin123 (hasheada por Django) - NO USAR EN PRODUCCIÓN
    'pbkdf2_sha256$390000$Kl5De9YrqV7yAvJWzX3PgE$ZAm7ZxLHxyENzP4HaW3PyZ8CgzK9tKQHdw33QBYhvyg=', 
    1, 
    'admin', 
    'Admin', 
    'Principal', 
    'admin@ejemplo.com', 
    1, 
    1, 
    NOW()
);

-- Insertar eventos de ejemplo
INSERT INTO events (name, description, event_date, location, capacity, created_at, updated_at)
VALUES 
('Concierto de Rock', 'Un increíble concierto con las mejores bandas de rock de la región.', DATE_ADD(NOW(), INTERVAL 7 DAY), 'Arena Principal, Pasto', 500, NOW(), NOW()),
('Festival Gastronómico', 'Descubre los mejores sabores de la cocina colombiana.', DATE_ADD(NOW(), INTERVAL 14 DAY), 'Parque Central, Pasto', 300, NOW(), NOW()),
('Conferencia de Tecnología', 'Aprende sobre las últimas tendencias en tecnología y desarrollo.', DATE_ADD(NOW(), INTERVAL 21 DAY), 'Centro de Convenciones, Pasto', 200, NOW(), NOW());

-- Insertar tipos de entradas para los eventos
INSERT INTO ticket_types (event_id, name, price, available_quantity, created_at, updated_at)
VALUES
(1, 'VIP', 150000, 50, NOW(), NOW()),
(1, 'General', 80000, 200, NOW(), NOW()),
(1, 'Estudiante', 60000, 100, NOW(), NOW()),
(2, 'Premium', 100000, 50, NOW(), NOW()),
(2, 'Estándar', 50000, 150, NOW(), NOW()),
(3, 'Profesional', 200000, 100, NOW(), NOW()),
(3, 'Estudiante', 80000, 50, NOW(), NOW());