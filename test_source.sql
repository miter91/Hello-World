=== STORED PROCEDURE START ===
Database: VISTA_STAGING
Schema: dbo
Name: TestProcedure
CreateDate: 2024-01-01 10:00:00.000
ModifyDate: 2024-01-01 10:00:00.000
--- DEFINITION START ---
CREATE PROCEDURE [dbo].[TestProcedure]
    @UserID INT,
    @StartDate DATETIME
AS
BEGIN
    SELECT UserID, UserName, 
           CAST(CreateDate AS DATE) as CreateDate
    FROM Users
    WHERE UserID = @UserID
      AND CreateDate >= @StartDate
END
--- DEFINITION END ---
=== STORED PROCEDURE END ===

=== STORED PROCEDURE START ===
Database: VISTA_STAGING
Schema: dbo
Name: GetOrderData
CreateDate: 2024-01-01 10:00:00.000
ModifyDate: 2024-01-01 10:00:00.000
--- DEFINITION START ---
CREATE PROCEDURE [dbo].[GetOrderData]
    @OrderID INT
AS
BEGIN
    SELECT * FROM Orders WHERE OrderID = @OrderID
END
--- DEFINITION END ---
=== STORED PROCEDURE END ===
