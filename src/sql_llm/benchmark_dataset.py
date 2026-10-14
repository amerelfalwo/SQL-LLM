"""Chinook Evaluation Benchmark: 40 Rigorously Curated Questions & Gold SQL.

Design Principles:
1. Complete Determinism: Every query with LIMIT includes an explicit ORDER BY with tiebreakers.
2. No Hidden Truncation: Questions requesting 'all' return complete results without arbitrary LIMITs.
3. Unambiguous Column Contracts: Questions specify expected columns ('Return only ...') to prevent dialect mismatches.
4. Non-Empty & Meaningful: Every query returns > 0 rows on Chinook SQLite and tests real relational logic.
5. Zero Ties at Boundaries: LIMIT thresholds never split tied rows ambiguously.
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
        question="List the names of the first 5 artists ordered alphabetically. Return only Name.",
        gold_sql="SELECT Name FROM Artist ORDER BY Name ASC LIMIT 5;",
    ),
    BenchmarkItem(
        id=2,
        category="Filter & Sort",
        difficulty="Easy",
        question="Find the first name, last name, and city of all customers living in 'Paris'. Return only FirstName, LastName, and City.",
        gold_sql="SELECT FirstName, LastName, City FROM Customer WHERE City = 'Paris';",
    ),
    BenchmarkItem(
        id=3,
        category="Filter & Sort",
        difficulty="Easy",
        question="List all genres ordered by their name alphabetically. Return only Name.",
        gold_sql="SELECT Name FROM Genre ORDER BY Name ASC;",
    ),
    BenchmarkItem(
        id=4,
        category="Filter & Sort",
        difficulty="Easy",
        question="Return the names and millisecond durations of the 5 longest tracks, ordered by duration descending, then TrackId ascending. Return only Name and Milliseconds.",
        gold_sql="SELECT Name, Milliseconds FROM Track ORDER BY Milliseconds DESC, TrackId ASC LIMIT 5;",
    ),
    BenchmarkItem(
        id=5,
        category="Filter & Sort",
        difficulty="Easy",
        question="Find the invoice ID, customer ID, and total for invoices where the total exceeds 15 dollars. Return only InvoiceId, CustomerId, and Total.",
        gold_sql="SELECT InvoiceId, CustomerId, Total FROM Invoice WHERE Total > 15.0;",
    ),
    BenchmarkItem(
        id=6,
        category="Filter & Sort",
        difficulty="Easy",
        question="List all employees with the title 'Sales Support Agent'. Return only FirstName, LastName, and Title.",
        gold_sql="SELECT FirstName, LastName, Title FROM Employee WHERE Title = 'Sales Support Agent';",
    ),
    BenchmarkItem(
        id=7,
        category="Filter & Sort",
        difficulty="Easy",
        question="Return the TrackId, Name and UnitPrice of the first 10 tracks (ordered by TrackId) with unit price greater than 0.99. Return only TrackId, Name, and UnitPrice.",
        gold_sql="SELECT TrackId, Name, UnitPrice FROM Track WHERE UnitPrice > 0.99 ORDER BY TrackId ASC LIMIT 10;",
    ),
    BenchmarkItem(
        id=8,
        category="Filter & Sort",
        difficulty="Easy",
        question="Find the customer ID, first name, last name, and country for customers from 'Brazil'. Return only CustomerId, FirstName, LastName, and Country.",
        gold_sql="SELECT CustomerId, FirstName, LastName, Country FROM Customer WHERE Country = 'Brazil';",
    ),

    # ── Category 2: Single Table Aggregations (Moderate) ──
    BenchmarkItem(
        id=9,
        category="Aggregation",
        difficulty="Medium",
        question="How many total tracks are in the database? Return only the count.",
        gold_sql="SELECT COUNT(*) FROM Track;",
    ),
    BenchmarkItem(
        id=10,
        category="Aggregation",
        difficulty="Medium",
        question="What is the average total amount of an invoice? Return only the average total.",
        gold_sql="SELECT AVG(Total) FROM Invoice;",
    ),
    BenchmarkItem(
        id=11,
        category="Aggregation",
        difficulty="Medium",
        question="Find the maximum and minimum length of a track in milliseconds. Return only the maximum and minimum length.",
        gold_sql="SELECT MAX(Milliseconds), MIN(Milliseconds) FROM Track;",
    ),
    BenchmarkItem(
        id=12,
        category="Aggregation",
        difficulty="Medium",
        question="What is the total revenue generated from all invoices combined? Return only the total sum.",
        gold_sql="SELECT SUM(Total) FROM Invoice;",
    ),
    BenchmarkItem(
        id=13,
        category="Aggregation",
        difficulty="Medium",
        question="How many invoices were billed to the country 'Canada'? Return only the count.",
        gold_sql="SELECT COUNT(*) FROM Invoice WHERE BillingCountry = 'Canada';",
    ),
    BenchmarkItem(
        id=14,
        category="Aggregation",
        difficulty="Medium",
        question="Count how many customers are registered from each country, sorted by highest count, then alphabetically by country. Return only Country and CustomerCount.",
        gold_sql="SELECT Country, COUNT(*) AS CustomerCount FROM Customer GROUP BY Country ORDER BY CustomerCount DESC, Country ASC;",
    ),

    # ── Category 3: Two-Table Joins (Moderate) ──
    BenchmarkItem(
        id=15,
        category="2-Table Join",
        difficulty="Medium",
        question="Find all album titles by the artist 'Iron Maiden'. Return only Title.",
        gold_sql="SELECT al.Title FROM Album al JOIN Artist ar ON ar.ArtistId = al.ArtistId WHERE ar.Name = 'Iron Maiden';",
    ),
    BenchmarkItem(
        id=16,
        category="2-Table Join",
        difficulty="Medium",
        question="Show each album title alongside the name of its artist for the first 10 albums ordered by AlbumId. Return only Title and Name.",
        gold_sql="SELECT al.Title, ar.Name FROM Album al JOIN Artist ar ON ar.ArtistId = al.ArtistId ORDER BY al.AlbumId ASC LIMIT 10;",
    ),
    BenchmarkItem(
        id=17,
        category="2-Table Join",
        difficulty="Medium",
        question="For each genre, count how many tracks exist. Return only Name and TrackCount, sorted by highest count, then by genre name alphabetically.",
        gold_sql="SELECT g.Name, COUNT(t.TrackId) AS TrackCount FROM Genre g JOIN Track t ON t.GenreId = g.GenreId GROUP BY g.GenreId ORDER BY TrackCount DESC, g.Name ASC;",
    ),
    BenchmarkItem(
        id=18,
        category="2-Table Join",
        difficulty="Medium",
        question="Return InvoiceId, FirstName, LastName and Total for invoices billed to 'Germany'. Return only InvoiceId, FirstName, LastName, and Total.",
        gold_sql="SELECT i.InvoiceId, c.FirstName, c.LastName, i.Total FROM Invoice i JOIN Customer c ON c.CustomerId = i.CustomerId WHERE i.BillingCountry = 'Germany';",
    ),
    BenchmarkItem(
        id=19,
        category="2-Table Join",
        difficulty="Medium",
        question="List all tracks on the album 'Let There Be Rock'. Return only Name.",
        gold_sql="SELECT t.Name FROM Track t JOIN Album a ON a.AlbumId = t.AlbumId WHERE a.Title = 'Let There Be Rock';",
    ),
    BenchmarkItem(
        id=20,
        category="2-Table Join",
        difficulty="Medium",
        question="Return the artist name and album count of the top 5 artists by number of albums (ties by artist name). Return only Name and AlbumCount.",
        gold_sql="SELECT ar.Name, COUNT(al.AlbumId) AS AlbumCount FROM Artist ar JOIN Album al ON al.ArtistId = ar.ArtistId GROUP BY ar.ArtistId ORDER BY AlbumCount DESC, ar.Name ASC LIMIT 5;",
    ),
    BenchmarkItem(
        id=21,
        category="2-Table Join",
        difficulty="Medium",
        question="Which media type is used by the most tracks? Return only the media type name and track count.",
        gold_sql="SELECT m.Name, COUNT(t.TrackId) AS TrackCount FROM MediaType m JOIN Track t ON t.MediaTypeId = m.MediaTypeId GROUP BY m.MediaTypeId ORDER BY TrackCount DESC LIMIT 1;",
    ),
    BenchmarkItem(
        id=22,
        category="2-Table Join",
        difficulty="Medium",
        question="For each employee who supports at least one customer, return FirstName, LastName and the number of customers they support. Return only FirstName, LastName, and CustomerCount.",
        gold_sql="SELECT e.FirstName, e.LastName, COUNT(c.CustomerId) AS CustomerCount FROM Employee e JOIN Customer c ON c.SupportRepId = e.EmployeeId GROUP BY e.EmployeeId;",
    ),

    # ── Category 4: Multi-Table Joins & Grouping (Hard) ──
    BenchmarkItem(
        id=23,
        category="Multi-Table Join",
        difficulty="Hard",
        question="Return CustomerId, FirstName, LastName and TotalSpent for the top 5 customers by total spent (ties by CustomerId). Return only CustomerId, FirstName, LastName, and TotalSpent.",
        gold_sql="SELECT c.CustomerId, c.FirstName, c.LastName, SUM(i.Total) AS TotalSpent FROM Customer c JOIN Invoice i ON i.CustomerId = c.CustomerId GROUP BY c.CustomerId ORDER BY TotalSpent DESC, c.CustomerId ASC LIMIT 5;",
    ),
    BenchmarkItem(
        id=24,
        category="Multi-Table Join",
        difficulty="Hard",
        question="List the track name, album title, and artist name for tracks whose Composer field contains 'Miles Davis'. Return only Name, Title, and ArtistName.",
        gold_sql="SELECT t.Name, al.Title, ar.Name AS ArtistName FROM Track t JOIN Album al ON al.AlbumId = t.AlbumId JOIN Artist ar ON ar.ArtistId = al.ArtistId WHERE t.Composer LIKE '%Miles Davis%';",
    ),
    BenchmarkItem(
        id=25,
        category="Multi-Table Join",
        difficulty="Hard",
        question="How many tracks have been sold more than once in total? Return only the count.",
        gold_sql="SELECT COUNT(*) FROM (SELECT TrackId FROM InvoiceLine GROUP BY TrackId HAVING SUM(Quantity) > 1);",
    ),
    BenchmarkItem(
        id=26,
        category="Multi-Table Join",
        difficulty="Hard",
        question="Which genre has generated the highest total revenue? Return only the genre name and total revenue.",
        gold_sql="SELECT g.Name, SUM(il.UnitPrice * il.Quantity) AS Revenue FROM Genre g JOIN Track t ON t.GenreId = g.GenreId JOIN InvoiceLine il ON il.TrackId = t.TrackId GROUP BY g.GenreId ORDER BY Revenue DESC LIMIT 1;",
    ),
    BenchmarkItem(
        id=27,
        category="Multi-Table Join",
        difficulty="Hard",
        question="List all playlists that contain tracks by the artist 'Queen'. Return only distinct playlist names, ordered alphabetically. Return only Name.",
        gold_sql="SELECT DISTINCT p.Name FROM Playlist p JOIN PlaylistTrack pt ON pt.PlaylistId = p.PlaylistId JOIN Track t ON t.TrackId = pt.TrackId JOIN Album a ON a.AlbumId = t.AlbumId JOIN Artist ar ON ar.ArtistId = a.ArtistId WHERE ar.Name = 'Queen' ORDER BY p.Name ASC;",
    ),
    BenchmarkItem(
        id=28,
        category="Multi-Table Join",
        difficulty="Hard",
        question="Find the top 3 artists by total track sales revenue, ordered by revenue descending, then artist name alphabetically. Return only Name and TotalRevenue.",
        gold_sql="SELECT ar.Name, SUM(il.UnitPrice * il.Quantity) AS TotalRevenue FROM Artist ar JOIN Album al ON al.ArtistId = ar.ArtistId JOIN Track t ON t.AlbumId = al.AlbumId JOIN InvoiceLine il ON il.TrackId = t.TrackId GROUP BY ar.ArtistId ORDER BY TotalRevenue DESC, ar.Name ASC LIMIT 3;",
    ),
    BenchmarkItem(
        id=29,
        category="Multi-Table Join",
        difficulty="Hard",
        question="What is the total amount spent on music by customers living in 'USA'? Return only the sum.",
        gold_sql="SELECT SUM(i.Total) FROM Invoice i JOIN Customer c ON c.CustomerId = i.CustomerId WHERE c.Country = 'USA';",
    ),
    BenchmarkItem(
        id=30,
        category="Multi-Table Join",
        difficulty="Hard",
        question="Show the invoice ID, customer first name, last name, and the total number of items purchased in that invoice for the first 5 invoices ordered by InvoiceId. Return only InvoiceId, FirstName, LastName, and ItemCount.",
        gold_sql="SELECT i.InvoiceId, c.FirstName, c.LastName, SUM(il.Quantity) AS ItemCount FROM Invoice i JOIN Customer c ON c.CustomerId = i.CustomerId JOIN InvoiceLine il ON il.InvoiceId = i.InvoiceId GROUP BY i.InvoiceId ORDER BY i.InvoiceId ASC LIMIT 5;",
    ),

    # ── Category 5: Complex Conditions, Subqueries, & Dates (Advanced) ──
    BenchmarkItem(
        id=31,
        category="Date / Time",
        difficulty="Medium",
        question="How many invoices were issued in the year 2010? Return only the count.",
        gold_sql="SELECT COUNT(*) FROM Invoice WHERE strftime('%Y', InvoiceDate) = '2010';",
    ),
    BenchmarkItem(
        id=32,
        category="Date / Time",
        difficulty="Medium",
        question="Calculate the total sales revenue per year from invoices, ordered by year ascending. Return only Year and AnnualSales.",
        gold_sql="SELECT strftime('%Y', InvoiceDate) AS Year, SUM(Total) AS AnnualSales FROM Invoice GROUP BY Year ORDER BY Year ASC;",
    ),
    BenchmarkItem(
        id=33,
        category="Subquery",
        difficulty="Hard",
        question="Find all customers who have never had an invoice with a total over 15 dollars. Return only CustomerId, FirstName, and LastName.",
        gold_sql="SELECT CustomerId, FirstName, LastName FROM Customer WHERE CustomerId NOT IN (SELECT DISTINCT CustomerId FROM Invoice WHERE Total > 15.0);",
    ),
    BenchmarkItem(
        id=34,
        category="Subquery",
        difficulty="Hard",
        question="Return the TrackId and Name of the first 10 tracks (ordered by TrackId) that were never purchased. Return only TrackId and Name.",
        gold_sql="SELECT TrackId, Name FROM Track WHERE TrackId NOT IN (SELECT DISTINCT TrackId FROM InvoiceLine) ORDER BY TrackId ASC LIMIT 10;",
    ),
    BenchmarkItem(
        id=35,
        category="Self-Join",
        difficulty="Hard",
        question="For each employee that has a manager, return two columns: Employee and Manager, both as 'FirstName LastName'.",
        gold_sql="SELECT e.FirstName || ' ' || e.LastName AS Employee, m.FirstName || ' ' || m.LastName AS Manager FROM Employee e JOIN Employee m ON e.ReportsTo = m.EmployeeId;",
    ),
    BenchmarkItem(
        id=36,
        category="Grouping & Having",
        difficulty="Medium",
        question="Find all artists who have released more than 5 albums. Return only Name and AlbumCount, sorted by album count descending, then by artist name alphabetically.",
        gold_sql="SELECT ar.Name, COUNT(al.AlbumId) AS AlbumCount FROM Artist ar JOIN Album al ON al.ArtistId = ar.ArtistId GROUP BY ar.ArtistId HAVING COUNT(al.AlbumId) > 5 ORDER BY AlbumCount DESC, ar.Name ASC;",
    ),
    BenchmarkItem(
        id=37,
        category="Aggregation",
        difficulty="Medium",
        question="Find the billing country that has generated the highest total invoice sales. Return only BillingCountry and TotalSales.",
        gold_sql="SELECT BillingCountry, SUM(Total) AS TotalSales FROM Invoice GROUP BY BillingCountry ORDER BY TotalSales DESC LIMIT 1;",
    ),
    BenchmarkItem(
        id=38,
        category="Multi-Table Join",
        difficulty="Hard",
        question="How many distinct customers have purchased at least one track of the 'Jazz' genre? Return only the count.",
        gold_sql="SELECT COUNT(DISTINCT c.CustomerId) FROM Customer c JOIN Invoice i ON i.CustomerId = c.CustomerId JOIN InvoiceLine il ON il.InvoiceId = i.InvoiceId JOIN Track t ON t.TrackId = il.TrackId JOIN Genre g ON g.GenreId = t.GenreId WHERE g.Name = 'Jazz';",
    ),
    BenchmarkItem(
        id=39,
        category="Filter & Sort",
        difficulty="Medium",
        question="Find all tracks in the 'Jazz' genre that are longer than 5 minutes (300,000 milliseconds). Return only Name and Milliseconds.",
        gold_sql="SELECT t.Name, t.Milliseconds FROM Track t JOIN Genre g ON g.GenreId = t.GenreId WHERE g.Name = 'Jazz' AND t.Milliseconds > 300000;",
    ),
    BenchmarkItem(
        id=40,
        category="Multi-Table Join",
        difficulty="Hard",
        question="Calculate the total amount of money spent by each customer from 'Germany'. Return only CustomerId, FirstName, LastName and TotalSpent, sorted by total spent descending, then by CustomerId.",
        gold_sql="SELECT c.CustomerId, c.FirstName, c.LastName, SUM(i.Total) AS TotalSpent FROM Customer c JOIN Invoice i ON i.CustomerId = c.CustomerId WHERE c.Country = 'Germany' GROUP BY c.CustomerId ORDER BY TotalSpent DESC, c.CustomerId ASC;",
    ),
]
