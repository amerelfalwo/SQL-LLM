"""Chinook Evaluation Benchmark: 40 Curated Questions & Gold SQL Queries.

Covers:
- Simple SELECT, filtering, ORDER BY, LIMIT
- Single-table aggregations (COUNT, SUM, AVG, MIN, MAX)
- 2-table, 3-table, and 4-table JOINs
- GROUP BY, HAVING, ORDER BY DESC
- Date filters and string matching
All queries are executable on SQLite and verified against data/Chinook_Sqlite.sqlite.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class BenchmarkItem:
    id: int
    category: str
    difficulty: str
    question: str
    gold_sql: str


CHINOOK_BENCHMARK: list[BenchmarkItem] = [
    # ── Category 1: Single Table Filtering & Ordering (Simple) ──
    BenchmarkItem(
        id=1,
        category="Filter & Sort",
        difficulty="Easy",
        question="List the names of the first 5 artists ordered alphabetically.",
        gold_sql="SELECT Name FROM Artist ORDER BY Name ASC LIMIT 5;",
    ),
    BenchmarkItem(
        id=2,
        category="Filter & Sort",
        difficulty="Easy",
        question="Find the first name, last name, and city of all customers living in 'Paris'.",
        gold_sql="SELECT FirstName, LastName, City FROM Customer WHERE City = 'Paris';",
    ),
    BenchmarkItem(
        id=3,
        category="Filter & Sort",
        difficulty="Easy",
        question="List all genres ordered by their name alphabetically.",
        gold_sql="SELECT Name FROM Genre ORDER BY Name ASC;",
    ),
    BenchmarkItem(
        id=4,
        category="Filter & Sort",
        difficulty="Easy",
        question="Return the names and millisecond durations of the 5 longest tracks.",
        gold_sql="SELECT Name, Milliseconds FROM Track ORDER BY Milliseconds DESC LIMIT 5;",
    ),
    BenchmarkItem(
        id=5,
        category="Filter & Sort",
        difficulty="Easy",
        question="Find the invoice ID, customer ID, and total for invoices where the total exceeds 15 dollars.",
        gold_sql="SELECT InvoiceId, CustomerId, Total FROM Invoice WHERE Total > 15.0 ORDER BY Total DESC;",
    ),
    BenchmarkItem(
        id=6,
        category="Filter & Sort",
        difficulty="Easy",
        question="List all employees with the title 'Sales Support Agent'.",
        gold_sql="SELECT FirstName, LastName, Title FROM Employee WHERE Title = 'Sales Support Agent';",
    ),
    BenchmarkItem(
        id=7,
        category="Filter & Sort",
        difficulty="Easy",
        question="Find all tracks that have a unit price greater than 0.99.",
        gold_sql="SELECT Name, UnitPrice FROM Track WHERE UnitPrice > 0.99 LIMIT 10;",
    ),
    BenchmarkItem(
        id=8,
        category="Filter & Sort",
        difficulty="Easy",
        question="Find the customer ID, first name, last name, and country for customers from 'Brazil'.",
        gold_sql="SELECT CustomerId, FirstName, LastName, Country FROM Customer WHERE Country = 'Brazil';",
    ),

    # ── Category 2: Single Table Aggregations (Moderate) ──
    BenchmarkItem(
        id=9,
        category="Aggregation",
        difficulty="Medium",
        question="How many total tracks are in the database?",
        gold_sql="SELECT COUNT(*) FROM Track;",
    ),
    BenchmarkItem(
        id=10,
        category="Aggregation",
        difficulty="Medium",
        question="What is the average total amount of an invoice?",
        gold_sql="SELECT AVG(Total) FROM Invoice;",
    ),
    BenchmarkItem(
        id=11,
        category="Aggregation",
        difficulty="Medium",
        question="Find the maximum and minimum length of a track in milliseconds.",
        gold_sql="SELECT MAX(Milliseconds), MIN(Milliseconds) FROM Track;",
    ),
    BenchmarkItem(
        id=12,
        category="Aggregation",
        difficulty="Medium",
        question="What is the total revenue generated from all invoices combined?",
        gold_sql="SELECT SUM(Total) FROM Invoice;",
    ),
    BenchmarkItem(
        id=13,
        category="Aggregation",
        difficulty="Medium",
        question="How many invoices were billed to the country 'Canada'?",
        gold_sql="SELECT COUNT(*) FROM Invoice WHERE BillingCountry = 'Canada';",
    ),
    BenchmarkItem(
        id=14,
        category="Aggregation",
        difficulty="Medium",
        question="Count how many customers are registered from each country, sorted by highest count.",
        gold_sql="SELECT Country, COUNT(*) AS CustomerCount FROM Customer GROUP BY Country ORDER BY CustomerCount DESC;",
    ),

    # ── Category 3: Two-Table Joins (Moderate) ──
    BenchmarkItem(
        id=15,
        category="2-Table Join",
        difficulty="Medium",
        question="Find all album titles by the artist 'Iron Maiden'.",
        gold_sql="SELECT al.Title FROM Album al JOIN Artist ar ON ar.ArtistId = al.ArtistId WHERE ar.Name = 'Iron Maiden';",
    ),
    BenchmarkItem(
        id=16,
        category="2-Table Join",
        difficulty="Medium",
        question="Show each album title alongside the name of its artist for the first 10 albums.",
        gold_sql="SELECT al.Title, ar.Name FROM Album al JOIN Artist ar ON ar.ArtistId = al.ArtistId LIMIT 10;",
    ),
    BenchmarkItem(
        id=17,
        category="2-Table Join",
        difficulty="Medium",
        question="For each genre, count how many tracks exist. Return the genre name and count, highest first.",
        gold_sql="SELECT g.Name, COUNT(t.TrackId) AS TrackCount FROM Genre g JOIN Track t ON t.GenreId = g.GenreId GROUP BY g.GenreId ORDER BY TrackCount DESC;",
    ),
    BenchmarkItem(
        id=18,
        category="2-Table Join",
        difficulty="Medium",
        question="Show the invoice ID, total, and full customer name (first and last) for invoices billed to 'Germany'.",
        gold_sql="SELECT i.InvoiceId, c.FirstName, c.LastName, i.Total FROM Invoice i JOIN Customer c ON c.CustomerId = i.CustomerId WHERE i.BillingCountry = 'Germany';",
    ),
    BenchmarkItem(
        id=19,
        category="2-Table Join",
        difficulty="Medium",
        question="List all tracks on the album 'Let There Be Rock'.",
        gold_sql="SELECT t.Name FROM Track t JOIN Album a ON a.AlbumId = t.AlbumId WHERE a.Title = 'Let There Be Rock';",
    ),
    BenchmarkItem(
        id=20,
        category="2-Table Join",
        difficulty="Medium",
        question="Find the top 5 artists with the most albums.",
        gold_sql="SELECT ar.Name, COUNT(al.AlbumId) AS AlbumCount FROM Artist ar JOIN Album al ON al.ArtistId = ar.ArtistId GROUP BY ar.ArtistId ORDER BY AlbumCount DESC LIMIT 5;",
    ),
    BenchmarkItem(
        id=21,
        category="2-Table Join",
        difficulty="Medium",
        question="Which media type is used by the most tracks? Return the media type name and track count.",
        gold_sql="SELECT m.Name, COUNT(t.TrackId) AS TrackCount FROM MediaType m JOIN Track t ON t.MediaTypeId = m.MediaTypeId GROUP BY m.MediaTypeId ORDER BY TrackCount DESC LIMIT 1;",
    ),
    BenchmarkItem(
        id=22,
        category="2-Table Join",
        difficulty="Medium",
        question="Show the employee first name, last name, and how many customers each supports.",
        gold_sql="SELECT e.FirstName, e.LastName, COUNT(c.CustomerId) AS CustomerCount FROM Employee e JOIN Customer c ON c.SupportRepId = e.EmployeeId GROUP BY e.EmployeeId;",
    ),

    # ── Category 4: Multi-Table Joins & Grouping (Hard) ──
    BenchmarkItem(
        id=23,
        category="Multi-Table Join",
        difficulty="Hard",
        question="Find the top 5 customers who spent the most total money across all invoices.",
        gold_sql="SELECT c.CustomerId, c.FirstName, c.LastName, SUM(i.Total) AS TotalSpent FROM Customer c JOIN Invoice i ON i.CustomerId = c.CustomerId GROUP BY c.CustomerId ORDER BY TotalSpent DESC LIMIT 5;",
    ),
    BenchmarkItem(
        id=24,
        category="Multi-Table Join",
        difficulty="Hard",
        question="List the track name, album title, and artist name for tracks composed by 'Miles Davis'.",
        gold_sql="SELECT t.Name, al.Title, ar.Name FROM Track t JOIN Album al ON al.AlbumId = t.AlbumId JOIN Artist ar ON ar.ArtistId = al.ArtistId WHERE t.Composer LIKE '%Miles Davis%';",
    ),
    BenchmarkItem(
        id=25,
        category="Multi-Table Join",
        difficulty="Hard",
        question="Find the top 5 bestselling tracks based on total quantity sold across all invoice lines.",
        gold_sql="SELECT t.Name, SUM(il.Quantity) AS TotalSold FROM Track t JOIN InvoiceLine il ON il.TrackId = t.TrackId GROUP BY t.TrackId ORDER BY TotalSold DESC LIMIT 5;",
    ),
    BenchmarkItem(
        id=26,
        category="Multi-Table Join",
        difficulty="Hard",
        question="Which genre has generated the highest total revenue? Return the genre name and total revenue.",
        gold_sql="SELECT g.Name, SUM(il.UnitPrice * il.Quantity) AS Revenue FROM Genre g JOIN Track t ON t.GenreId = g.GenreId JOIN InvoiceLine il ON il.TrackId = t.TrackId GROUP BY g.GenreId ORDER BY Revenue DESC LIMIT 1;",
    ),
    BenchmarkItem(
        id=27,
        category="Multi-Table Join",
        difficulty="Hard",
        question="List all playlists that contain tracks by the artist 'Queen'. Return distinct playlist names.",
        gold_sql="SELECT DISTINCT p.Name FROM Playlist p JOIN PlaylistTrack pt ON pt.PlaylistId = p.PlaylistId JOIN Track t ON t.TrackId = pt.TrackId JOIN Album a ON a.AlbumId = t.AlbumId JOIN Artist ar ON ar.ArtistId = a.ArtistId WHERE ar.Name = 'Queen';",
    ),
    BenchmarkItem(
        id=28,
        category="Multi-Table Join",
        difficulty="Hard",
        question="Find the top 3 artists by total track sales revenue.",
        gold_sql="SELECT ar.Name, SUM(il.UnitPrice * il.Quantity) AS TotalRevenue FROM Artist ar JOIN Album al ON al.ArtistId = ar.ArtistId JOIN Track t ON t.AlbumId = al.AlbumId JOIN InvoiceLine il ON il.TrackId = t.TrackId GROUP BY ar.ArtistId ORDER BY TotalRevenue DESC LIMIT 3;",
    ),
    BenchmarkItem(
        id=29,
        category="Multi-Table Join",
        difficulty="Hard",
        question="What is the total amount spent on music by customers living in 'USA'?",
        gold_sql="SELECT SUM(i.Total) FROM Invoice i JOIN Customer c ON c.CustomerId = i.CustomerId WHERE c.Country = 'USA';",
    ),
    BenchmarkItem(
        id=30,
        category="Multi-Table Join",
        difficulty="Hard",
        question="Show the invoice ID, customer first name, last name, and the total number of items purchased in that invoice for the first 5 invoices.",
        gold_sql="SELECT i.InvoiceId, c.FirstName, c.LastName, SUM(il.Quantity) AS ItemCount FROM Invoice i JOIN Customer c ON c.CustomerId = i.CustomerId JOIN InvoiceLine il ON il.InvoiceId = i.InvoiceId GROUP BY i.InvoiceId LIMIT 5;",
    ),

    # ── Category 5: Complex Conditions, Subqueries, & Dates (Advanced) ──
    BenchmarkItem(
        id=31,
        category="Date / Time",
        difficulty="Medium",
        question="How many invoices were issued in the year 2010?",
        gold_sql="SELECT COUNT(*) FROM Invoice WHERE strftime('%Y', InvoiceDate) = '2010';",
    ),
    BenchmarkItem(
        id=32,
        category="Date / Time",
        difficulty="Medium",
        question="Calculate the total sales revenue per year from invoices, ordered by year.",
        gold_sql="SELECT strftime('%Y', InvoiceDate) AS Year, SUM(Total) AS AnnualSales FROM Invoice GROUP BY Year ORDER BY Year ASC;",
    ),
    BenchmarkItem(
        id=33,
        category="Subquery",
        difficulty="Hard",
        question="Find all customers who have never had an invoice with a total over 15 dollars.",
        gold_sql="SELECT CustomerId, FirstName, LastName FROM Customer WHERE CustomerId NOT IN (SELECT DISTINCT CustomerId FROM Invoice WHERE Total > 15.0) LIMIT 10;",
    ),
    BenchmarkItem(
        id=34,
        category="Subquery",
        difficulty="Hard",
        question="Find all tracks that have never been purchased on any invoice.",
        gold_sql="SELECT TrackId, Name FROM Track WHERE TrackId NOT IN (SELECT DISTINCT TrackId FROM InvoiceLine) LIMIT 10;",
    ),
    BenchmarkItem(
        id=35,
        category="Self-Join",
        difficulty="Hard",
        question="List each employee along with the full name of their direct manager.",
        gold_sql="SELECT e.FirstName || ' ' || e.LastName AS Employee, m.FirstName || ' ' || m.LastName AS Manager FROM Employee e JOIN Employee m ON e.ReportsTo = m.EmployeeId;",
    ),
    BenchmarkItem(
        id=36,
        category="Grouping & Having",
        difficulty="Medium",
        question="Find all artists who have released more than 5 albums.",
        gold_sql="SELECT ar.Name, COUNT(al.AlbumId) AS AlbumCount FROM Artist ar JOIN Album al ON al.ArtistId = ar.ArtistId GROUP BY ar.ArtistId HAVING COUNT(al.AlbumId) > 5 ORDER BY AlbumCount DESC;",
    ),
    BenchmarkItem(
        id=37,
        category="Aggregation",
        difficulty="Medium",
        question="Find the country that has generated the highest total invoice sales.",
        gold_sql="SELECT BillingCountry, SUM(Total) AS TotalSales FROM Invoice GROUP BY BillingCountry ORDER BY TotalSales DESC LIMIT 1;",
    ),
    BenchmarkItem(
        id=38,
        category="Multi-Table Join",
        difficulty="Hard",
        question="Find the customer who has bought the largest number of distinct tracks.",
        gold_sql="SELECT c.CustomerId, c.FirstName, c.LastName, COUNT(DISTINCT il.TrackId) AS UniqueTracks FROM Customer c JOIN Invoice i ON i.CustomerId = c.CustomerId JOIN InvoiceLine il ON il.InvoiceId = i.InvoiceId GROUP BY c.CustomerId ORDER BY UniqueTracks DESC LIMIT 1;",
    ),
    BenchmarkItem(
        id=39,
        category="Filter & Sort",
        difficulty="Medium",
        question="Find all tracks in the 'Jazz' genre that are longer than 5 minutes (300,000 milliseconds).",
        gold_sql="SELECT t.Name, t.Milliseconds FROM Track t JOIN Genre g ON g.GenreId = t.GenreId WHERE g.Name = 'Jazz' AND t.Milliseconds > 300000 ORDER BY t.Milliseconds DESC;",
    ),
    BenchmarkItem(
        id=40,
        category="Multi-Table Join",
        difficulty="Hard",
        question="Calculate the total amount of money spent by each customer from 'Germany', sorted by total spending descending.",
        gold_sql="SELECT c.CustomerId, c.FirstName, c.LastName, SUM(i.Total) AS TotalSpent FROM Customer c JOIN Invoice i ON i.CustomerId = c.CustomerId WHERE c.Country = 'Germany' GROUP BY c.CustomerId ORDER BY TotalSpent DESC;",
    ),
]
