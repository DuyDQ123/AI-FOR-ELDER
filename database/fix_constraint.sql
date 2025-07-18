-- Fix constraint issue: remove old constraint and add correct one
USE medicine_dispenser;

-- Drop existing constraint (MySQL syntax)
ALTER TABLE medicines DROP INDEX medicines_unique_compartment;

-- Add correct constraint (user_id + compartment_number should be unique)
ALTER TABLE medicines ADD CONSTRAINT medicines_unique_compartment UNIQUE (user_id, compartment_number);

-- Check current data
SELECT user_id, compartment_number, name FROM medicines ORDER BY user_id, compartment_number;