-- Default expense categories (Spanish display names).
-- Slugs are stable identifiers shared across locales (used in MCP calls and DB).
-- Persons and projects are created at install time via add-member.sh or the agent.

INSERT OR IGNORE INTO categories (slug, name) VALUES
  ('comida', 'Comida'),
  ('supermercado', 'Supermercado'),
  ('restaurante', 'Restaurante'),
  ('transporte', 'Transporte'),
  ('salud', 'Salud'),
  ('farmacia', 'Farmacia'),
  ('impuestos', 'Impuestos'),
  ('servicios', 'Servicios'),
  ('alquiler', 'Alquiler'),
  ('hipoteca', 'Hipoteca'),
  ('mascotas', 'Mascotas'),
  ('hogar', 'Hogar'),
  ('viajes', 'Viajes'),
  ('tecnologia', 'Tecnología'),
  ('educacion', 'Educación');
