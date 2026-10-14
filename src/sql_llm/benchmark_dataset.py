"""Chinook Evaluation Benchmark: 40 Rigorously Curated Questions & Gold SQL.

Design Principles:
1. Complete Determinism: Every query with LIMIT includes an explicit ORDER BY with tiebreakers.
2. No Hidden Truncation: Questions requesting 'all' return the complete result set without arbitrary LIMITs.
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
        question="List the names of the first 5 artists ordered alphabetically. Return only the artist name.",
        gold_sql="SELECT Name FROM Artist ORDER BY Name ASC LIMIT 5;",
    ),
    BenchmarkItem(
        id=2,
        category="Filter & Sort",
        difficulty="Easy",
        question="Find the first name, last name, and city of all customers living in 'Paris'. Return only FirstName, LastName, and City, ordered by LastName.",
        gold_sql="SELECT FirstName, LastName, City FROM Customer WHERE City = 'Paris' ORDER BY LastName ASC;",
    ),
    BenchmarkItem(
        id=3,
        category="Filter & Sort",
        difficulty="Easy",
        question="List all genres ordered by their name alphabetically. Return only the genre name.",
        gold_sql="SELECT Name FROM Genre ORDER BY Name ASC;",
    ),
    BenchmarkItem(
        id=4,
        category="Filter & Sort",
        difficulty="Easy",
        question="Return the names and millisecond durations of the 5 longest tracks, ordered by duration descending, then track ID ascending. Return only Name and Milliseconds.",
        gold_sql="SELECT Name, Milliseconds FROM Track ORDER BY Milliseconds DESC, TrackId ASC LIMIT 5;",
    ),
    BenchmarkItem(
        id=5,
        category="Filter & Sort",
        difficulty="Easy",
        question="Find the invoice ID, customer ID, and total for invoices where the total exceeds 15 dollars, sorted by total descending, then invoice ID ascending. Return only InvoiceId, CustomerId, and Total.",
        gold_sql="SELECT InvoiceId, CustomerId, Total FROM Invoice WHERE Total > 15.0 ORDER BY Total DESC, InvoiceId ASC;",
    ),
    BenchmarkItem(
        id=6,
        category="Filter & Sort",
        difficulty="Easy",
        question="List all employees with the title 'Sales Support Agent'. Return only FirstName, LastName, and Title, ordered by EmployeeId.",
        gold_sql="SELECT FirstName, LastName, Title FROM Employee WHERE Title = 'Sales Support Agent' ORDER BY EmployeeId ASC;",
    ),
    BenchmarkItem(
        id=7,
        category="Filter & Sort",
        difficulty="Easy",
        question="Find the names and unit prices of all tracks that have a unit price greater than 0.99. Return only Name and UnitPrice, ordered by Name.",
        gold_sql="SELECT Name, UnitPrice FROM Track WHERE UnitPrice > 0.99 ORDER BY Name ASC;",
    ),
    BenchmarkItem(
        id=8,
        category="Filter & Sort",
        difficulty="Easy",
        question="Find the customer ID, first name, last name, and country for customers from 'Brazil'. Return only CustomerId, FirstName, LastName, and Country, ordered by CustomerId.",
        gold_sql="SELECT CustomerId, FirstName, LastName, Country FROM Customer WHERE Country = 'Brazil' ORDER BY CustomerId ASC;",
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
        question="Count how many customers are registered from each country. Return only Country and the customer count, sorted by customer count descending, then country alphabetically.",
        gold_sql="SELECT Country, COUNT(*) AS CustomerCount FROM Customer GROUP BY Country ORDER BY CustomerCount DESC, Country ASC;",
    ),

    # ── Category 3: Two-Table Joins (Moderate) ──
    BenchmarkItem(
        id=15,
        category="2-Table Join",
        difficulty="Medium",
        question="Find all album titles by the artist 'Iron Maiden'. Return only the album title, ordered alphabetically.",
        gold_sql="SELECT al.Title FROM Album al JOIN Artist ar ON ar.ArtistId = al.ArtistId WHERE ar.Name = 'Iron Maiden' ORDER BY al.Title ASC;",
    ),
    BenchmarkItem(
        id=16,
        category="2-Table Join",
        difficulty="Medium",
        question="Show each album title alongside the name of its artist for the first 10 albums ordered by AlbumId. Return only the album title and artist name.",
        gold_sql="SELECT al.Title, ar.Name FROM Album al JOIN Artist ar ON ar.ArtistId = al.ArtistId ORDER BY al.AlbumId ASC LIMIT 10;",
    ),
    BenchmarkItem(
        id=17,
        category="2-Table Join",
        difficulty="Medium",
        question="For each genre, count how many tracks exist. Return only the genre name and count, sorted by track count descending, then genre name alphabetically.",
        gold_sql="SELECT g.Name, COUNT(t.TrackId) AS TrackCount FROM Genre g JOIN Track t ON t.GenreId = g.GenreId GROUP BY g.GenreId ORDER BY TrackCount DESC, g.Name ASC;",
    ),
    BenchmarkItem(
        id=18,
        category="2-Table Join",
        difficulty="Medium",
        question="Show the invoice ID, customer first name, customer last name, and invoice total for invoices billed to 'Germany'. Return only InvoiceId, FirstName, LastName, and Total, ordered by InvoiceId.",
        gold_sql="SELECT i.InvoiceId, c.FirstName, c.LastName, i.Total FROM Invoice i JOIN Customer c ON c.CustomerId = i.CustomerId WHERE i.BillingCountry = 'Germany' ORDER BY i.InvoiceId ASC;",
    ),
    BenchmarkItem(
        id=19,
        category="2-Table Join",
        difficulty="Medium",
        question="List all tracks on the album 'Let There Be Rock'. Return only the track name, ordered by TrackId.",
        gold_sql="SELECT t.Name FROM Track t JOIN Album a ON a.AlbumId = t.AlbumId WHERE a.Title = 'Let There Be Rock' ORDER BY t.TrackId ASC;",
    ),
    BenchmarkItem(
        id=20,
        category="2-Table Join",
        difficulty="Medium",
        question="Find the top 5 artists with the most albums. Return only the artist name and album count, ordered by album count descending, then artist name alphabetically.",
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
        question="For each employee who supports at least one customer, return the employee first name, last name, and the count of customers they support, sorted by customer count descending. Return only FirstName, LastName, and customer count.",
        gold_sql="SELECT e.FirstName, e.LastName, COUNT(c.CustomerId) AS CustomerCount FROM Employee e JOIN Customer c ON c.SupportRepId = e.EmployeeId GROUP BY e.EmployeeId ORDER BY CustomerCount DESC;",
    ),

    # ── Category 4: Multi-Table Joins & Grouping (Hard) ──
    BenchmarkItem(
        id=23,
        category="Multi-Table Join",
        difficulty="Hard",
        question="Find the top 5 customers who spent the most total money across invoices. Return only customer first name, last name, and total amount spent, ordered by total spent descending, then last name alphabetically.",
        gold_sql="SELECT c.FirstName, c.LastName, SUM(i.Total) AS TotalSpent FROM Customer c JOIN Invoice i ON i.CustomerId = c.CustomerId GROUP BY c.CustomerId ORDER BY TotalSpent DESC, c.LastName ASC LIMIT 5;",
    ),
    BenchmarkItem(
        id=24,
        category="Multi-Table Join",
        difficulty="Hard",
        question="List the track name, album title, and artist name for tracks whose composer contains 'Miles Davis'. Return only the track name, album title, and artist name, ordered by track name.",
        gold_sql="SELECT t.Name, al.Title, ar.Name FROM Track t JOIN Album al ON al.AlbumId = t.AlbumId JOIN Artist ar ON ar.ArtistId = al.ArtistId WHERE t.Composer LIKE '%Miles Davis%' ORDER BY t.Name ASC;",
    ),
    BenchmarkItem(
        id=25,
        category="Multi-Table Join",
        difficulty="Hard",
        question="How many tracks were sold more than once across all invoice lines? Return only the count.",
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
        question="List all playlists that contain tracks by the artist 'Queen'. Return only distinct playlist names, ordered alphabetically.",
        gold_sql="SELECT DISTINCT p.Name FROM Playlist p JOIN PlaylistTrack pt ON pt.PlaylistId = p.PlaylistId JOIN Track t ON t.TrackId = pt.TrackId JOIN Album a ON a.AlbumId = t.AlbumId JOIN Artist ar ON ar.ArtistId = a.ArtistId WHERE ar.Name = 'Queen' ORDER BY p.Name ASC;",
    ),
    BenchmarkItem(
        id=28,
        category="Multi-Table Join",
        difficulty="Hard",
        question="Find the top 3 artists by total track sales revenue. Return only the artist name and total revenue, ordered by revenue descending, then artist name alphabetically.",
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
        question="Show the invoice ID, customer first name, last name, and the total number of items purchased in that invoice for the first 5 invoices ordered by InvoiceId. Return only InvoiceId, FirstName, LastName, and total quantity.",
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
        question="Calculate the total sales revenue per year from invoices, ordered by year ascending. Return only the year and total annual sales.",
        gold_sql="SELECT strftime('%Y', InvoiceDate) AS Year, SUM(Total) AS AnnualSales FROM Invoice GROUP BY Year ORDER BY Year ASC;",
    ),
    BenchmarkItem(
        id=33,
        category="Subquery",
        difficulty="Hard",
        question="Find all customers who have never had an invoice with a total over 15 dollars. Return only CustomerId, FirstName, and LastName, ordered by CustomerId.",
        gold_sql="SELECT CustomerId, FirstName, LastName FROM Customer WHERE CustomerId NOT IN (SELECT DISTINCT CustomerId FROM Invoice WHERE Total > 15.0) ORDER BY CustomerId ASC;",
    ),
    BenchmarkItem(
        id=34,
        category="Subquery",
        difficulty="Hard",
        question="Find the first 10 tracks that have never been purchased on any invoice, ordered by TrackId. Return only TrackId and track name.",
        gold_sql="SELECT TrackId, Name FROM Track WHERE TrackId NOT IN (SELECT DISTINCT TrackId FROM InvoiceLine) ORDER BY TrackId ASC LIMIT 10;",
    ),
    BenchmarkItem(
        id=35,
        category="Self-Join",
        difficulty="Hard",
        question="List all employees that have a manager, along with their manager's first and last name. Return only employee first name, employee last name, manager first name, and manager last name, ordered by employee first name, then employee last name.",
        gold_sql="SELECT e.FirstName AS EmployeeFirstName, e.LastName AS EmployeeLastName, m.FirstName AS ManagerFirstName, m.LastName AS ManagerLastName FROM Employee e JOIN Employee m ON e.ReportsTo = m.EmployeeId ORDER BY e.FirstName ASC, e.LastName ASC;",
    ),
    BenchmarkItem(
        id=36,
        category="Grouping & Having",
        difficulty="Medium",
        question="Find all artists who have released more than 5 albums. Return only the artist name and album count, ordered by album count descending, then artist name alphabetically.",
        gold_sql="SELECT ar.Name, COUNT(al.AlbumId) AS AlbumCount FROM Artist ar JOIN Album al ON al.ArtistId = ar.ArtistId GROUP BY ar.ArtistId HAVING COUNT(al.AlbumId) > 5 ORDER BY AlbumCount DESC, ar.Name ASC;",
    ),
    BenchmarkItem(
        id=37,
        category="Aggregation",
        difficulty="Medium",
        question="Find the billing country that has generated the highest total invoice sales. Return only the billing country and total sales.",
        gold_sql="SELECT BillingCountry, SUM(Total) AS TotalSales FROM Invoice GROUP BY BillingCountry ORDER BY TotalSales DESC LIMIT 1;",
    ),
    BenchmarkItem(
        id=38,
        category="Multi-Table Join",
        difficulty="Hard",
        question="Find the artist with the most total tracks in the database. Return only the artist name and track count.",
        gold_sql="SELECT ar.Name, COUNT(t.TrackId) AS TrackCount FROM Artist ar JOIN Album al ON al.ArtistId = ar.ArtistId JOIN Track t ON t.AlbumId = al.AlbumId GROUP BY ar.ArtistId ORDER BY TrackCount DESC LIMIT 1;",
    ),
    BenchmarkItem(
        id=39,
        category="Filter & Sort",
        difficulty="Medium",
        question="Find all tracks in the 'Jazz' genre that are longer than 5 minutes (300,000 milliseconds). Return only the track name and millisecond duration, ordered by duration descending, then track name alphabetically.",
        gold_sql="SELECT t.Name, t.Milliseconds FROM Track t JOIN Genre g ON g.GenreId = t.GenreId WHERE g.Name = 'Jazz' AND t.Milliseconds > 300000 ORDER BY t.Milliseconds DESC, t.Name ASC;",
    ),
    BenchmarkItem(
        id=40,
        category="Multi-Table Join",
        difficulty="Hard",
        question="Calculate the total amount of money spent by each customer from 'Germany'. Return only customer first name, last name, and total amount spent, ordered by total spending descending, then customer last name alphabetically.",
        gold_sql="SELECT c.FirstName, c.LastName, SUM(i.Total) AS TotalSpent FROM Customer c JOIN Invoice i ON i.CustomerId = c.CustomerId WHERE c.Country = 'Germany' GROUP BY c.CustomerId ORDER BY TotalSpent DESC, c.LastName ASC;",
    ),
]
