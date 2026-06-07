-- Default expense categories (English display names).
-- Same slugs as seed-categories-es.sql — stable IDs for MCP and existing data.

INSERT OR IGNORE INTO categories (slug, name) VALUES
  ('comida', 'Food'),
  ('supermercado', 'Groceries'),
  ('restaurante', 'Dining out'),
  ('transporte', 'Transport'),
  ('salud', 'Health'),
  ('farmacia', 'Pharmacy'),
  ('impuestos', 'Taxes'),
  ('servicios', 'Utilities & services'),
  ('alquiler', 'Rent'),
  ('hipoteca', 'Mortgage'),
  ('mascotas', 'Pets'),
  ('hogar', 'Home'),
  ('viajes', 'Travel'),
  ('tecnologia', 'Technology'),
  ('educacion', 'Education');
