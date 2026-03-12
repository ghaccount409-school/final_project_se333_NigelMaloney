# from fastmcp import FastMCP

# def main():
   
#     mcp = FastMCP("Demo 🚀")

#     @mcp.tool
#     def add(a: int, b: int) -> int:
#         """Add two numbers"""
#         return a + b

# if __name__ == "__main__":
#     # IMPORTANT: Use SSE transport so VS Code can connect via URL.
#     mcp.run(transport="sse")

from mcp.server.fastmcp import FastMCP

#from fastmcp import FastMCP  

#import fastmcp


#mcp = fastmcp("Demo 🚀")
mcp = FastMCP("Demo 🚀")

#@mcp.tool
@mcp.tool()
def add(a: int, b: int) -> int:
    """Add two numbers"""
    return a + b

if __name__ == "__main__":
    # IMPORTANT: Use SSE transport so VS Code can connect via URL.
    mcp.run(transport="sse")
