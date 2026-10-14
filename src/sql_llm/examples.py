"""Example questions with gold SQL for the Chinook database.

Shared by the web UI (suggestion chips) and the CLI benchmark (scoring).
Questions name the expected columns explicitly so result-set comparison is fair.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class Example:
    question: str
    gold_sql: str


EXAMPLES: list[Example] = [
    Example(
        "List the names of the first 5 artists ordered alphabetically. Return only the name.",
        "SELECT Name FROM Artist ORDER BY Name LIMIT 5",
    ),
    Example(
        "Return the titles of all albums by the artist 'AC/DC'.",
        "SELECT al.Title FROM Album al JOIN Artist ar ON ar.ArtistId = al.ArtistId WHERE ar.Name = 'AC/DC'",
    ),
    Example(
        "For each genre return the genre name and the number of tracks, highest count first.",
        "SELECT g.Name, COUNT(*) FROM Track t JOIN Genre g ON g.GenreId = t.GenreId "
        "GROUP BY g.GenreId ORDER BY 2 DESC",
    ),
    Example(
        "Return the first name, last name and total invoice amount of the 5 customers who spent the most.",
        "SELECT c.FirstName, c.LastName, SUM(i.Total) FROM Customer c JOIN Invoice i "
        "ON i.CustomerId = c.CustomerId GROUP BY c.CustomerId ORDER BY SUM(i.Total) DESC LIMIT 5",
    ),
    Example(
        "Return the name and milliseconds of the 5 longest tracks.",
        "SELECT Name, Milliseconds FROM Track ORDER BY Milliseconds DESC LIMIT 5",
    ),
    Example(
        "Return the invoice id, customer first name, last name and invoice total for invoices billed to the USA.",
        "SELECT i.InvoiceId, c.FirstName, c.LastName, i.Total FROM Invoice i JOIN Customer c "
        "ON c.CustomerId = i.CustomerId WHERE i.BillingCountry = 'USA'",
    ),
]
