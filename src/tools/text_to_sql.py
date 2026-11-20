import asyncio

from app.services.query_service import run_query

from server import mcp


@mcp.tool()
async def text_to_sql(question: str) -> str:
    """Answer a natural-language financial question by generating and running SQL.

    Converts the question into SQL against real financial data (currently
    Futwork's metrics), executes it, and returns a plain-English answer.
    Always runs fresh against the live database (no caching).

    Args:
        question: The natural-language financial question to answer, e.g.
            "what was Futwork's total revenue in March 2026?".
    """
    result = await asyncio.to_thread(run_query, question)

    if result["company_detection_error"]:
        raise ValueError(result["company_detection_error"])
    if result["validation_error"]:
        raise ValueError(result["validation_error"])
    if result["execution_error"]:
        raise ValueError(result["execution_error"])

    return f"{result['final_answer']}\n\n(SQL used: {result['generated_sql']})"
