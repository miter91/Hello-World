-- SQL Script to Extract All Stored Procedures from a Database
-- Instructions: Run this script in SQL Server Management Studio
-- Replace 'YOUR_DATABASE_NAME' with the actual database name (VISTA_STAGING or VISTA_REPORTING)
-- The output will be saved to a file on the server

SET NOCOUNT ON;

DECLARE @DatabaseName NVARCHAR(128) = 'YOUR_DATABASE_NAME'; -- Change this to your database name
DECLARE @OutputPath NVARCHAR(500) = 'C:\Temp\' + @DatabaseName + '_StoredProcs_' + 
                                     CONVERT(VARCHAR(8), GETDATE(), 112) + '_' +
                                     REPLACE(CONVERT(VARCHAR(8), GETDATE(), 108), ':', '') + '.txt';

-- Create temporary table to store results
CREATE TABLE #StoredProcedures (
    DatabaseName NVARCHAR(128),
    SchemaName NVARCHAR(128),
    ProcedureName NVARCHAR(128),
    ProcedureDefinition NVARCHAR(MAX),
    CreateDate DATETIME,
    ModifyDate DATETIME
);

-- Switch to the target database and extract stored procedures
DECLARE @SQL NVARCHAR(MAX) = '
USE [' + @DatabaseName + '];
INSERT INTO #StoredProcedures
SELECT 
    DB_NAME() AS DatabaseName,
    SCHEMA_NAME(p.schema_id) AS SchemaName,
    p.name AS ProcedureName,
    m.definition AS ProcedureDefinition,
    p.create_date AS CreateDate,
    p.modify_date AS ModifyDate
FROM sys.procedures p
INNER JOIN sys.sql_modules m ON p.object_id = m.object_id
WHERE p.is_ms_shipped = 0
ORDER BY SCHEMA_NAME(p.schema_id), p.name;
';

EXEC sp_executesql @SQL;

-- Format output with clear delimiters
SELECT 
    '=== STORED PROCEDURE START ===' + CHAR(13) + CHAR(10) +
    'Database: ' + DatabaseName + CHAR(13) + CHAR(10) +
    'Schema: ' + SchemaName + CHAR(13) + CHAR(10) +
    'Name: ' + ProcedureName + CHAR(13) + CHAR(10) +
    'CreateDate: ' + CONVERT(VARCHAR(30), CreateDate, 121) + CHAR(13) + CHAR(10) +
    'ModifyDate: ' + CONVERT(VARCHAR(30), ModifyDate, 121) + CHAR(13) + CHAR(10) +
    '--- DEFINITION START ---' + CHAR(13) + CHAR(10) +
    ProcedureDefinition + CHAR(13) + CHAR(10) +
    '--- DEFINITION END ---' + CHAR(13) + CHAR(10) +
    '=== STORED PROCEDURE END ===' + CHAR(13) + CHAR(10) + CHAR(13) + CHAR(10)
FROM #StoredProcedures
ORDER BY SchemaName, ProcedureName;

-- Clean up
DROP TABLE #StoredProcedures;

-- Print output path
PRINT 'Results displayed above. Please copy the output and save to a file.';
PRINT 'Suggested filename: ' + @OutputPath;

/*
ALTERNATIVE METHOD: Using BCP to export directly to file (requires xp_cmdshell enabled)

-- Enable xp_cmdshell (requires sysadmin permissions)
-- EXEC sp_configure 'show advanced options', 1;
-- RECONFIGURE;
-- EXEC sp_configure 'xp_cmdshell', 1;
-- RECONFIGURE;

-- Export using BCP
DECLARE @BCPCommand VARCHAR(8000);
SET @BCPCommand = 'bcp "SELECT ''=== STORED PROCEDURE START ==='' + CHAR(13) + CHAR(10) + ' +
                  '''Database: '' + DatabaseName + CHAR(13) + CHAR(10) + ' +
                  '''Schema: '' + SchemaName + CHAR(13) + CHAR(10) + ' +
                  '''Name: '' + ProcedureName + CHAR(13) + CHAR(10) + ' +
                  '''CreateDate: '' + CONVERT(VARCHAR(30), CreateDate, 121) + CHAR(13) + CHAR(10) + ' +
                  '''ModifyDate: '' + CONVERT(VARCHAR(30), ModifyDate, 121) + CHAR(13) + CHAR(10) + ' +
                  '''--- DEFINITION START ---'' + CHAR(13) + CHAR(10) + ' +
                  'ProcedureDefinition + CHAR(13) + CHAR(10) + ' +
                  '''--- DEFINITION END ---'' + CHAR(13) + CHAR(10) + ' +
                  '''=== STORED PROCEDURE END ==='' + CHAR(13) + CHAR(10) + CHAR(13) + CHAR(10) ' +
                  'FROM #StoredProcedures ORDER BY SchemaName, ProcedureName" ' +
                  'queryout "' + @OutputPath + '" -c -T -S' + @@SERVERNAME;

EXEC xp_cmdshell @BCPCommand;
*/
