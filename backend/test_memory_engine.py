from memory_engine import MemoryEngine

if __name__ == "__main__":
    engine = MemoryEngine()

    # Add some memories
    engine.add_memory("I love football.")
    engine.add_memory("I enjoy watching cricket.")
    engine.add_memory("I ate pasta yesterday.")
    engine.add_memory("Football is my favorite sport.")

    # Search for similar memories
    print("Searching for similar memories to 'I like soccer':")
    distances, indices = engine.search_memory("I like soccer", k=2)
    print(f"Distances: {distances}")
    print(f"Indices: {indices}")
