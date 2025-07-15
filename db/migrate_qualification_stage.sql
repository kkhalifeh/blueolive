-- Migration to add qualification_stage field to Customers table
-- Run this script to update the database schema

ALTER TABLE Customers 
ADD COLUMN qualification_stage VARCHAR(50) DEFAULT 'initial';

-- Update existing customers to have initial stage
UPDATE Customers SET qualification_stage = 'initial' WHERE qualification_stage IS NULL;

-- Create index for better performance
CREATE INDEX idx_customers_qualification_stage ON Customers (qualification_stage);

-- Add a comment to document the field
COMMENT ON COLUMN Customers.qualification_stage IS 'Tracks customer qualification progress: initial, budget_collected, bedrooms_collected, location_collected, contact_info_collected';