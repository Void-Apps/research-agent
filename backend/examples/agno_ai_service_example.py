"""
Example usage of Agno AI service for research synthesis and analysis
"""
import asyncio
import logging
from datetime import datetime
from typing import Dict, List

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.agno_ai_service import AgnoAIService
from models.research import SourceResult, SourceType

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def create_sample_research_data() -> Dict[str, List[SourceResult]]:
    """Create sample research data for demonstration"""
    
    # Google Scholar results
    scholar_results = [
        SourceResult(
            title="Deep Learning Applications in Medical Diagnosis",
            authors=["Dr. Sarah Chen", "Prof. Michael Rodriguez"],
            abstract="This comprehensive study examines the implementation of deep learning algorithms in medical diagnostic systems, focusing on image recognition and pattern analysis for early disease detection.",
            url="https://scholar.google.com/citations?view_op=view_citation&hl=en&user=example1",
            publication_date=datetime(2023, 6, 15),
            source_type=SourceType.GOOGLE_SCHOLAR,
            citation_count=245
        ),
        SourceResult(
            title="Machine Learning Ethics in Healthcare: A Systematic Review",
            authors=["Dr. Emily Watson", "Dr. James Liu", "Prof. Anna Kowalski"],
            abstract="A systematic review of ethical considerations in machine learning applications within healthcare systems, addressing bias, privacy, and transparency concerns.",
            url="https://scholar.google.com/citations?view_op=view_citation&hl=en&user=example2",
            publication_date=datetime(2023, 4, 22),
            source_type=SourceType.GOOGLE_SCHOLAR,
            citation_count=189
        )
    ]
    
    # ScienceDirect results
    sciencedirect_results = [
        SourceResult(
            title="AI-Powered Diagnostic Tools: Clinical Validation and Implementation",
            authors=["Dr. Robert Kim", "Dr. Lisa Thompson"],
            abstract="Clinical validation study of AI-powered diagnostic tools in real-world healthcare settings, measuring accuracy, efficiency, and user acceptance rates.",
            url="https://www.sciencedirect.com/science/article/pii/example1",
            publication_date=datetime(2023, 8, 10),
            source_type=SourceType.SCIENCEDIRECT,
            doi="10.1016/j.artmed.2023.08.001",
            journal="Artificial Intelligence in Medicine",
            access_status="Open Access"
        ),
        SourceResult(
            title="Regulatory Frameworks for Medical AI: International Perspectives",
            authors=["Prof. David Martinez", "Dr. Sophie Anderson"],
            abstract="Comparative analysis of regulatory frameworks for medical AI across different countries, examining approval processes and safety standards.",
            url="https://www.sciencedirect.com/science/article/pii/example2",
            publication_date=datetime(2023, 7, 5),
            source_type=SourceType.SCIENCEDIRECT,
            doi="10.1016/j.healthpol.2023.07.002",
            journal="Health Policy",
            access_status="Subscription Required"
        )
    ]
    
    # Google Books results
    books_results = [
        SourceResult(
            title="Healthcare AI: From Theory to Practice",
            authors=["Dr. Jennifer Park", "Prof. Thomas Wilson"],
            abstract="A comprehensive guide to implementing artificial intelligence solutions in healthcare environments, covering technical, ethical, and practical considerations.",
            url="https://books.google.com/books?id=example1",
            publication_date=datetime(2023, 2, 28),
            source_type=SourceType.GOOGLE_BOOKS,
            isbn="978-0123456789",
            preview_link="https://books.google.com/books/preview?id=example1"
        ),
        SourceResult(
            title="Machine Learning for Medical Professionals",
            authors=["Dr. Alex Johnson"],
            abstract="An accessible introduction to machine learning concepts and applications specifically designed for healthcare professionals without technical backgrounds.",
            url="https://books.google.com/books?id=example2",
            publication_date=datetime(2022, 11, 15),
            source_type=SourceType.GOOGLE_BOOKS,
            isbn="978-0987654321",
            preview_link="https://books.google.com/books/preview?id=example2"
        )
    ]
    
    return {
        "google_scholar": scholar_results,
        "sciencedirect": sciencedirect_results,
        "google_books": books_results
    }

async def demonstrate_research_synthesis():
    """Demonstrate research synthesis capabilities"""
    logger.info("=== Research Synthesis Demonstration ===")
    
    # Initialize AI service
    ai_service = AgnoAIService(model_name="gpt-4")
    
    # Create sample data
    research_data = await create_sample_research_data()
    query = "artificial intelligence applications in medical diagnosis"
    
    logger.info(f"Research Query: {query}")
    logger.info(f"Total Sources: {sum(len(results) for results in research_data.values())}")
    
    try:
        # Perform research synthesis
        synthesis = await ai_service.synthesize_research_results(query, research_data)
        
        logger.info("\n--- Synthesis Results ---")
        logger.info(f"Summary: {synthesis.summary}")
        logger.info(f"Confidence Score: {synthesis.confidence_score:.2f}")
        logger.info(f"Key Insights ({len(synthesis.key_insights)}):")
        for i, insight in enumerate(synthesis.key_insights, 1):
            logger.info(f"  {i}. {insight}")
        logger.info(f"Methodology: {synthesis.methodology_notes}")
        
        return synthesis
        
    except Exception as e:
        logger.error(f"Error in research synthesis: {e}")
        return None

async def demonstrate_quality_analysis():
    """Demonstrate quality analysis capabilities"""
    logger.info("\n=== Quality Analysis Demonstration ===")
    
    # Initialize AI service
    ai_service = AgnoAIService(model_name="gpt-4")
    
    # Create sample data and flatten results
    research_data = await create_sample_research_data()
    all_results = []
    for source_results in research_data.values():
        all_results.extend(source_results)
    
    logger.info(f"Analyzing quality of {len(all_results)} sources")
    
    try:
        # Perform quality analysis
        quality_analysis = await ai_service.analyze_research_quality(all_results)
        
        logger.info("\n--- Quality Analysis Results ---")
        logger.info(f"Overall Quality Score: {quality_analysis.overall_quality_score:.2f}")
        logger.info(f"Credibility Assessment: {quality_analysis.credibility_assessment}")
        logger.info(f"Recommendations ({len(quality_analysis.recommendations)}):")
        for i, rec in enumerate(quality_analysis.recommendations, 1):
            logger.info(f"  {i}. {rec}")
        
        if quality_analysis.source_scores:
            logger.info("Individual Source Scores:")
            for source, score in quality_analysis.source_scores.items():
                logger.info(f"  {source}: {score:.2f}")
        
        return quality_analysis
        
    except Exception as e:
        logger.error(f"Error in quality analysis: {e}")
        return None

async def demonstrate_relevance_scoring():
    """Demonstrate relevance scoring capabilities"""
    logger.info("\n=== Relevance Scoring Demonstration ===")
    
    # Initialize AI service
    ai_service = AgnoAIService(model_name="gpt-4")
    
    # Create sample data and flatten results
    research_data = await create_sample_research_data()
    all_results = []
    for source_results in research_data.values():
        all_results.extend(source_results)
    
    query = "AI medical diagnosis accuracy"
    logger.info(f"Scoring relevance for query: {query}")
    logger.info(f"Number of results to score: {len(all_results)}")
    
    try:
        # Perform relevance scoring
        relevance_scoring = await ai_service.score_relevance(query, all_results)
        
        logger.info("\n--- Relevance Scoring Results ---")
        logger.info(f"Explanation: {relevance_scoring.relevance_explanation}")
        logger.info(f"Filtering Criteria: {', '.join(relevance_scoring.filtering_criteria)}")
        
        logger.info("\nScored Results (ranked by relevance):")
        for item in relevance_scoring.scored_results[:5]:  # Show top 5
            result = item["result"]
            score = item["relevance_score"]
            rank = item["rank"]
            logger.info(f"  #{rank} (Score: {score:.2f}) - {result.title}")
            logger.info(f"      Authors: {', '.join(result.authors)}")
            logger.info(f"      Source: {result.source_type.value}")
        
        return relevance_scoring
        
    except Exception as e:
        logger.error(f"Error in relevance scoring: {e}")
        return None

async def demonstrate_insights_generation():
    """Demonstrate insights generation capabilities"""
    logger.info("\n=== Insights Generation Demonstration ===")
    
    # Initialize AI service
    ai_service = AgnoAIService(model_name="gpt-4")
    
    # Create sample synthesis and quality analysis
    synthesis = await demonstrate_research_synthesis()
    quality_analysis = await demonstrate_quality_analysis()
    
    if not synthesis or not quality_analysis:
        logger.error("Cannot generate insights without synthesis and quality analysis")
        return None
    
    query = "artificial intelligence in medical diagnosis"
    logger.info(f"Generating insights for query: {query}")
    
    try:
        # Generate insights
        insights = await ai_service.generate_research_insights(
            query, synthesis, quality_analysis
        )
        
        logger.info("\n--- Generated Insights ---")
        logger.info(f"Number of insights: {len(insights)}")
        for i, insight in enumerate(insights, 1):
            logger.info(f"  {i}. {insight}")
        
        return insights
        
    except Exception as e:
        logger.error(f"Error generating insights: {e}")
        return None

async def demonstrate_complete_workflow():
    """Demonstrate complete AI research workflow"""
    logger.info("\n" + "="*60)
    logger.info("COMPLETE AI RESEARCH WORKFLOW DEMONSTRATION")
    logger.info("="*60)
    
    # Initialize AI service
    ai_service = AgnoAIService(model_name="gpt-4")
    
    # Create sample data
    research_data = await create_sample_research_data()
    query = "AI applications in healthcare diagnosis and treatment"
    
    logger.info(f"Research Query: {query}")
    logger.info(f"Data Sources: {list(research_data.keys())}")
    logger.info(f"Total Results: {sum(len(results) for results in research_data.values())}")
    
    try:
        # Step 1: Research Synthesis
        logger.info("\n--- Step 1: Research Synthesis ---")
        synthesis = await ai_service.synthesize_research_results(query, research_data)
        logger.info(f"✓ Synthesis completed (Confidence: {synthesis.confidence_score:.2f})")
        
        # Step 2: Quality Analysis
        logger.info("\n--- Step 2: Quality Analysis ---")
        all_results = []
        for source_results in research_data.values():
            all_results.extend(source_results)
        
        quality_analysis = await ai_service.analyze_research_quality(all_results)
        logger.info(f"✓ Quality analysis completed (Score: {quality_analysis.overall_quality_score:.2f})")
        
        # Step 3: Relevance Scoring
        logger.info("\n--- Step 3: Relevance Scoring ---")
        relevance_scoring = await ai_service.score_relevance(query, all_results)
        logger.info(f"✓ Relevance scoring completed ({len(relevance_scoring.scored_results)} results scored)")
        
        # Step 4: Insights Generation
        logger.info("\n--- Step 4: Insights Generation ---")
        insights = await ai_service.generate_research_insights(query, synthesis, quality_analysis)
        logger.info(f"✓ Insights generated ({len(insights)} actionable insights)")
        
        # Final Summary
        logger.info("\n--- WORKFLOW SUMMARY ---")
        logger.info(f"Research Summary: {synthesis.summary[:100]}...")
        logger.info(f"Top Insight: {insights[0] if insights else 'No insights generated'}")
        logger.info(f"Quality Assessment: {quality_analysis.credibility_assessment[:100]}...")
        logger.info(f"Most Relevant Result: {relevance_scoring.scored_results[0]['result'].title if relevance_scoring.scored_results else 'No results'}")
        
        logger.info("\n✓ Complete workflow demonstration finished successfully!")
        
        return {
            "synthesis": synthesis,
            "quality_analysis": quality_analysis,
            "relevance_scoring": relevance_scoring,
            "insights": insights
        }
        
    except Exception as e:
        logger.error(f"Error in complete workflow: {e}")
        return None

async def demonstrate_error_handling():
    """Demonstrate error handling and fallback mechanisms"""
    logger.info("\n=== Error Handling Demonstration ===")
    
    # Initialize AI service with invalid model to trigger fallbacks
    ai_service = AgnoAIService(model_name="invalid-model")
    
    # Create minimal sample data
    research_data = {
        "google_scholar": [
            SourceResult(
                title="Test Paper",
                authors=["Test Author"],
                abstract="Test abstract",
                source_type=SourceType.GOOGLE_SCHOLAR
            )
        ]
    }
    
    query = "test query"
    
    logger.info("Testing fallback mechanisms with invalid AI model...")
    
    try:
        # Test synthesis fallback
        synthesis = await ai_service.synthesize_research_results(query, research_data)
        logger.info(f"✓ Synthesis fallback: {synthesis.methodology_notes}")
        
        # Test quality analysis fallback
        quality_analysis = await ai_service.analyze_research_quality(list(research_data.values())[0])
        logger.info(f"✓ Quality analysis fallback: Score {quality_analysis.overall_quality_score}")
        
        # Test relevance scoring fallback
        relevance_scoring = await ai_service.score_relevance(query, list(research_data.values())[0])
        logger.info(f"✓ Relevance scoring fallback: {relevance_scoring.relevance_explanation}")
        
        # Test insights generation fallback
        insights = await ai_service.generate_research_insights(query, synthesis, quality_analysis)
        logger.info(f"✓ Insights generation fallback: {len(insights)} insights")
        
        logger.info("✓ All fallback mechanisms working correctly!")
        
    except Exception as e:
        logger.error(f"Error in fallback demonstration: {e}")

async def main():
    """Main demonstration function"""
    logger.info("Starting Agno AI Service Demonstration")
    logger.info("="*50)
    
    # Run individual demonstrations
    await demonstrate_research_synthesis()
    await demonstrate_quality_analysis()
    await demonstrate_relevance_scoring()
    await demonstrate_insights_generation()
    
    # Run complete workflow
    await demonstrate_complete_workflow()
    
    # Test error handling
    await demonstrate_error_handling()
    
    logger.info("\n" + "="*50)
    logger.info("Agno AI Service Demonstration Complete!")

if __name__ == "__main__":
    asyncio.run(main())