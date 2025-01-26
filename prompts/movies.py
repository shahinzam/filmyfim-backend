def create_recommendation_prompt(movie_title: str) -> str:
    return f"""As an expert film critic and recommendation specialist, suggest exactly 6 movies similar to '{movie_title}'.

    Consider these critical aspects in your analysis:

    1. Emotional Resonance & Atmosphere:
       - Similar emotional impact and mood
       - Matching atmospheric elements
       - Comparable pacing and tone
       - Visual and stylistic similarities

    2. Narrative Elements:
       - Related story structures and plot devices
       - Similar character dynamics and development
       - Matching thematic depth and complexity
       - Comparable plot twists and revelations

    3. Viewer Experience:
       - Similar emotional journeys for the audience
       - Matching intellectual engagement level
       - Comparable memorable moments
       - Related cinematic techniques

    4. Audience Behavior Patterns:
       - Movies frequently enjoyed by fans of '{movie_title}'
       - Films with high viewer overlap
       - Similar cult following or audience reception
       - Matching viewer satisfaction patterns

    5. Technical and Artistic Merit:
       - Similar directorial style
       - Comparable cinematography and visual effects
       - Matching production quality
       - Related musical scoring and sound design

    Provide exactly 6 movie titles that best match these criteria. Focus on creating a cohesive viewing experience similar to '{movie_title}'.
    
    Return ONLY the movie titles, one per line, without any additional text, numbers, or explanations.
    Ensure each recommendation truly captures the essence and appeal of the original film.
    Do not include the original movie in the recommendations.""" 