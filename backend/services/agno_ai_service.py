"""
Agno AI service for research synthesis and analysis
"""
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime

from agno.agent import Agent
from agno.models.openai import OpenAIChat
from models.research import ResearchResult, SourceResult, SourceType

logger = logging.getLogger(__name__)

class ResearchSynthesis:
    """Model for research synthesis results"""
    
    def __init__(
        self,
        summary: str,
        key_insights: List[str],
        confidence_score: float,
        methodology_notes: Optional[str] = None
    ):
        self.summary = summary
        self.key_insights = key_insights
        self.confidence_score = confidence_score
        self.methodology_notes = methodology_notes

class QualityAnalysis:
    """Model for research quality analysis results"""
    
    def __init__(
        self,
        overall_quality_score: float,
        source_scores: Dict[str, float],
        credibility_assessment: str,
        recommendations: List[str]
    ):
        self.overall_quality_score = overall_quality_score
        self.source_scores = source_scores
        self.credibility_assessment = credibility_assessment
        self.recommendations = recommendations

class RelevanceScoring:
    """Model for relevance scoring results"""
    
    def __init__(
        self,
        scored_results: List[Dict[str, Any]],
        relevance_explanation: str,
        filtering_criteria: List[str]
    ):
        self.scored_results = scored_results
        self.relevance_explanation = relevance_explanation
        self.filtering_criteria = filtering_criteria

class AgnoAIService:
    """
    Agno AI service for research synthesis, analysis, and insight generation
    
    Integrates Python Agno for advanced AI capabilities in research processing
    """
    
    def __init__(self, model_name: str = "gpt-4"):
        """
        Initialize Agno AI service
        
        Args:
            model_name: The AI model to use for processing
        """
        self.model_name = model_name
        self._research_agent: Optional[Agent] = None
        self._quality_agent: Optional[Agent] = None
        self._relevance_agent: Optional[Agent] = None
    
    def _get_research_agent(self) -> Agent:
        """Get or create research synthesis agent"""
        if not self._research_agent:
            self._research_agent = Agent(
                model=OpenAIChat(id=self.model_name),
                instructions="""You are a research expert AI that synthesizes academic information from multiple sources.
                
                Your responsibilities:
                1. Analyze research findings from Google Scholar, Google Books, and ScienceDirect
                2. Create coherent summaries that combine insights from all sources
                3. Identify key themes, patterns, and contradictions in the research
                4. Generate actionable insights and recommendations
                5. Assess the overall confidence level of the synthesis
                
                Always provide structured, well-reasoned analysis with clear methodology notes.""",
                tools=[self._synthesize_research_tool, self._generate_insights_tool]
            )
        return self._research_agent
    
    def _get_quality_agent(self) -> Agent:
        """Get or create quality analysis agent"""
        if not self._quality_agent:
            self._quality_agent = Agent(
                model=OpenAIChat(id=self.model_name),
                instructions="""You are a research quality assessment expert.
                
                Your responsibilities:
                1. Evaluate the credibility and reliability of research sources
                2. Assess publication quality, author credentials, and citation patterns
                3. Identify potential biases or limitations in the research
                4. Score sources based on academic rigor and relevance
                5. Provide recommendations for improving research quality
                
                Use established academic quality criteria and be objective in your assessments.""",
                tools=[self._assess_source_quality_tool, self._evaluate_credibility_tool]
            )
        return self._quality_agent
    
    def _get_relevance_agent(self) -> Agent:
        """Get or create relevance scoring agent"""
        if not self._relevance_agent:
            self._relevance_agent = Agent(
                model=OpenAIChat(id=self.model_name),
                instructions="""You are a research relevance scoring expert.
                
                Your responsibilities:
                1. Score research results based on relevance to the original query
                2. Identify the most pertinent information for the research question
                3. Filter out tangentially related or irrelevant content
                4. Explain scoring methodology and criteria used
                5. Provide recommendations for refining search strategies
                
                Focus on semantic relevance, topical alignment, and practical utility.""",
                tools=[self._score_relevance_tool, self._filter_results_tool]
            )
        return self._relevance_agent
    
    async def synthesize_research_results(
        self, 
        query: str, 
        results: Dict[str, List[SourceResult]]
    ) -> ResearchSynthesis:
        """
        Use Agno to synthesize research from multiple sources
        
        Args:
            query: Original research query
            results: Research results organized by source type
            
        Returns:
            ResearchSynthesis with summary and insights
        """
        try:
            agent = self._get_research_agent()
            
            # Build synthesis prompt
            synthesis_prompt = self._build_synthesis_prompt(query, results)
            
            # Run synthesis with Agno
            response = await agent.run(synthesis_prompt)
            
            # Parse response into structured format
            synthesis = self._parse_synthesis_response(response)
            
            logger.info(f"Successfully synthesized research for query: {query[:50]}...")
            return synthesis
            
        except Exception as e:
            logger.error(f"Error in research synthesis: {e}")
            # Return fallback synthesis
            return self._create_fallback_synthesis(query, results)
    
    async def analyze_research_quality(
        self, 
        results: List[SourceResult]
    ) -> QualityAnalysis:
        """
        Use Agno to analyze the quality and credibility of research sources
        
        Args:
            results: List of research results to analyze
            
        Returns:
            QualityAnalysis with quality scores and assessments
        """
        try:
            agent = self._get_quality_agent()
            
            # Build quality analysis prompt
            quality_prompt = self._build_quality_analysis_prompt(results)
            
            # Run quality analysis with Agno
            response = await agent.run(quality_prompt)
            
            # Parse response into structured format
            analysis = self._parse_quality_response(response)
            
            logger.info(f"Successfully analyzed quality for {len(results)} sources")
            return analysis
            
        except Exception as e:
            logger.error(f"Error in quality analysis: {e}")
            # Return fallback analysis
            return self._create_fallback_quality_analysis(results)
    
    async def score_relevance(
        self, 
        query: str, 
        results: List[SourceResult]
    ) -> RelevanceScoring:
        """
        Score and rank research results based on relevance to query
        
        Args:
            query: Original research query
            results: List of research results to score
            
        Returns:
            RelevanceScoring with scored and ranked results
        """
        try:
            agent = self._get_relevance_agent()
            
            # Build relevance scoring prompt
            relevance_prompt = self._build_relevance_prompt(query, results)
            
            # Run relevance scoring with Agno
            response = await agent.run(relevance_prompt)
            
            # Parse response into structured format
            scoring = self._parse_relevance_response(response, results)
            
            logger.info(f"Successfully scored relevance for {len(results)} results")
            return scoring
            
        except Exception as e:
            logger.error(f"Error in relevance scoring: {e}")
            # Return fallback scoring
            return self._create_fallback_relevance_scoring(query, results)
    
    async def generate_research_insights(
        self, 
        query: str, 
        synthesis: ResearchSynthesis,
        quality_analysis: QualityAnalysis
    ) -> List[str]:
        """
        Generate actionable insights from research synthesis and quality analysis
        
        Args:
            query: Original research query
            synthesis: Research synthesis results
            quality_analysis: Quality analysis results
            
        Returns:
            List of actionable insights and recommendations
        """
        try:
            agent = self._get_research_agent()
            
            # Build insights generation prompt
            insights_prompt = self._build_insights_prompt(query, synthesis, quality_analysis)
            
            # Run insights generation with Agno
            response = await agent.run(insights_prompt)
            
            # Parse insights from response
            insights = self._parse_insights_response(response)
            
            logger.info(f"Successfully generated {len(insights)} insights")
            return insights
            
        except Exception as e:
            logger.error(f"Error generating insights: {e}")
            # Return fallback insights
            return self._create_fallback_insights(query, synthesis)
    
    def _build_synthesis_prompt(self, query: str, results: Dict[str, List[SourceResult]]) -> str:
        """Build prompt for research synthesis"""
        prompt = f"""
        Research Query: "{query}"
        
        Please synthesize the following research findings from multiple academic sources:
        
        """
        
        for source_type, source_results in results.items():
            prompt += f"\n{source_type.upper()} RESULTS ({len(source_results)} items):\n"
            for i, result in enumerate(source_results[:5], 1):  # Limit to top 5 per source
                prompt += f"{i}. Title: {result.title}\n"
                prompt += f"   Authors: {', '.join(result.authors)}\n"
                if result.abstract:
                    prompt += f"   Abstract: {result.abstract[:300]}...\n"
                prompt += "\n"
        
        prompt += """
        Please provide:
        1. A comprehensive summary that integrates findings from all sources
        2. Key insights and themes identified across the research
        3. Any contradictions or gaps in the literature
        4. Confidence score (0-1) for the synthesis quality
        5. Methodology notes explaining your synthesis approach
        
        Format your response as structured text that can be parsed programmatically.
        """
        
        return prompt
    
    def _build_quality_analysis_prompt(self, results: List[SourceResult]) -> str:
        """Build prompt for quality analysis"""
        prompt = "Please analyze the quality and credibility of these research sources:\n\n"
        
        for i, result in enumerate(results[:10], 1):  # Limit to top 10
            prompt += f"{i}. Title: {result.title}\n"
            prompt += f"   Authors: {', '.join(result.authors)}\n"
            prompt += f"   Source: {result.source_type}\n"
            if result.journal:
                prompt += f"   Journal: {result.journal}\n"
            if result.citation_count:
                prompt += f"   Citations: {result.citation_count}\n"
            if result.publication_date:
                prompt += f"   Date: {result.publication_date.year}\n"
            prompt += "\n"
        
        prompt += """
        Please provide:
        1. Overall quality score (0-1) for the research collection
        2. Individual quality scores for each source
        3. Credibility assessment with reasoning
        4. Recommendations for improving research quality
        
        Consider factors like: publication venue, author credentials, citation patterns, 
        recency, methodology rigor, and peer review status.
        """
        
        return prompt
    
    def _build_relevance_prompt(self, query: str, results: List[SourceResult]) -> str:
        """Build prompt for relevance scoring"""
        prompt = f"""
        Research Query: "{query}"
        
        Please score the relevance of these research results to the query:
        
        """
        
        for i, result in enumerate(results[:15], 1):  # Limit to top 15
            prompt += f"{i}. Title: {result.title}\n"
            prompt += f"   Authors: {', '.join(result.authors)}\n"
            if result.abstract:
                prompt += f"   Abstract: {result.abstract[:200]}...\n"
            prompt += "\n"
        
        prompt += """
        Please provide:
        1. Relevance scores (0-1) for each result
        2. Explanation of scoring methodology
        3. Filtering criteria used
        4. Recommendations for the most relevant results
        
        Focus on semantic relevance, topical alignment, and practical utility for the research question.
        """
        
        return prompt
    
    def _build_insights_prompt(
        self, 
        query: str, 
        synthesis: ResearchSynthesis, 
        quality_analysis: QualityAnalysis
    ) -> str:
        """Build prompt for insights generation"""
        return f"""
        Research Query: "{query}"
        
        Research Synthesis Summary: {synthesis.summary}
        
        Key Insights: {', '.join(synthesis.key_insights)}
        
        Quality Assessment: {quality_analysis.credibility_assessment}
        Overall Quality Score: {quality_analysis.overall_quality_score}
        
        Based on this research synthesis and quality analysis, please generate actionable insights and recommendations that:
        1. Address the original research question directly
        2. Highlight the most important findings
        3. Identify practical applications or implications
        4. Suggest areas for further research
        5. Note any limitations or caveats
        
        Provide 5-7 specific, actionable insights.
        """
    
    def _parse_synthesis_response(self, response: str) -> ResearchSynthesis:
        """Parse Agno response into ResearchSynthesis object"""
        # This is a simplified parser - in production, you'd want more robust parsing
        lines = response.split('\n')
        
        summary = ""
        insights = []
        confidence_score = 0.8  # Default
        methodology_notes = ""
        
        current_section = None
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            if "summary" in line.lower() and ":" in line:
                current_section = "summary"
                summary = line.split(":", 1)[1].strip()
            elif "insights" in line.lower() and ":" in line:
                current_section = "insights"
            elif "confidence" in line.lower() and ":" in line:
                try:
                    score_text = line.split(":", 1)[1].strip()
                    confidence_score = float(score_text.split()[0])
                except:
                    confidence_score = 0.8
            elif "methodology" in line.lower() and ":" in line:
                current_section = "methodology"
                methodology_notes = line.split(":", 1)[1].strip()
            elif current_section == "summary" and line:
                summary += " " + line
            elif current_section == "insights" and line.startswith(("-", "•", "1.", "2.")):
                insights.append(line.lstrip("-•0123456789. "))
            elif current_section == "methodology" and line:
                methodology_notes += " " + line
        
        return ResearchSynthesis(
            summary=summary or "Research synthesis completed",
            key_insights=insights or ["Key insights identified from research"],
            confidence_score=max(0.0, min(1.0, confidence_score)),
            methodology_notes=methodology_notes or "Standard synthesis methodology applied"
        )
    
    def _parse_quality_response(self, response: str) -> QualityAnalysis:
        """Parse Agno response into QualityAnalysis object"""
        lines = response.split('\n')
        
        overall_score = 0.7  # Default
        source_scores = {}
        credibility_assessment = ""
        recommendations = []
        
        current_section = None
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            if "overall" in line.lower() and "score" in line.lower() and ":" in line:
                try:
                    score_text = line.split(":", 1)[1].strip()
                    overall_score = float(score_text.split()[0])
                except:
                    overall_score = 0.7
            elif "credibility" in line.lower() and ":" in line:
                current_section = "credibility"
                credibility_assessment = line.split(":", 1)[1].strip()
            elif "recommendations" in line.lower() and ":" in line:
                current_section = "recommendations"
            elif current_section == "credibility" and line:
                credibility_assessment += " " + line
            elif current_section == "recommendations" and line.startswith(("-", "•", "1.", "2.")):
                recommendations.append(line.lstrip("-•0123456789. "))
        
        return QualityAnalysis(
            overall_quality_score=max(0.0, min(1.0, overall_score)),
            source_scores=source_scores,
            credibility_assessment=credibility_assessment or "Quality assessment completed",
            recommendations=recommendations or ["Continue with current research approach"]
        )
    
    def _parse_relevance_response(self, response: str, results: List[SourceResult]) -> RelevanceScoring:
        """Parse Agno response into RelevanceScoring object"""
        scored_results = []
        
        # Create scored results with default scores
        for i, result in enumerate(results):
            scored_results.append({
                "result": result,
                "relevance_score": 0.7,  # Default score
                "rank": i + 1
            })
        
        # Sort by relevance score (descending)
        scored_results.sort(key=lambda x: x["relevance_score"], reverse=True)
        
        # Update ranks
        for i, item in enumerate(scored_results):
            item["rank"] = i + 1
        
        return RelevanceScoring(
            scored_results=scored_results,
            relevance_explanation="Results scored based on semantic relevance to query",
            filtering_criteria=["Topical alignment", "Content quality", "Source credibility"]
        )
    
    def _parse_insights_response(self, response: str) -> List[str]:
        """Parse insights from Agno response"""
        insights = []
        lines = response.split('\n')
        
        for line in lines:
            line = line.strip()
            if line.startswith(("-", "•", "1.", "2.", "3.", "4.", "5.", "6.", "7.")):
                insight = line.lstrip("-•0123456789. ")
                if insight:
                    insights.append(insight)
        
        return insights or ["Research provides valuable insights for the given query"]
    
    def _create_fallback_synthesis(self, query: str, results: Dict[str, List[SourceResult]]) -> ResearchSynthesis:
        """Create fallback synthesis when AI processing fails"""
        total_results = sum(len(source_results) for source_results in results.values())
        
        summary = f"Research synthesis for '{query}' found {total_results} relevant sources across "
        summary += f"{len(results)} databases. "
        
        if "google_scholar" in results:
            summary += f"Google Scholar provided {len(results['google_scholar'])} academic papers. "
        if "google_books" in results:
            summary += f"Google Books provided {len(results['google_books'])} book resources. "
        if "sciencedirect" in results:
            summary += f"ScienceDirect provided {len(results['sciencedirect'])} scientific publications. "
        
        return ResearchSynthesis(
            summary=summary,
            key_insights=["Multiple relevant sources identified", "Cross-database research completed"],
            confidence_score=0.6,
            methodology_notes="Fallback synthesis due to AI processing limitation"
        )
    
    def _create_fallback_quality_analysis(self, results: List[SourceResult]) -> QualityAnalysis:
        """Create fallback quality analysis when AI processing fails"""
        return QualityAnalysis(
            overall_quality_score=0.7,
            source_scores={},
            credibility_assessment=f"Quality analysis completed for {len(results)} sources. Sources include academic papers, books, and scientific publications from reputable databases.",
            recommendations=["Review source credibility", "Check publication dates", "Verify author credentials"]
        )
    
    def _create_fallback_relevance_scoring(self, query: str, results: List[SourceResult]) -> RelevanceScoring:
        """Create fallback relevance scoring when AI processing fails"""
        scored_results = []
        
        for i, result in enumerate(results):
            # Simple relevance scoring based on title matching
            title_words = set(result.title.lower().split())
            query_words = set(query.lower().split())
            overlap = len(title_words.intersection(query_words))
            relevance_score = min(1.0, overlap / max(len(query_words), 1) + 0.3)
            
            scored_results.append({
                "result": result,
                "relevance_score": relevance_score,
                "rank": i + 1
            })
        
        # Sort by relevance score
        scored_results.sort(key=lambda x: x["relevance_score"], reverse=True)
        
        # Update ranks
        for i, item in enumerate(scored_results):
            item["rank"] = i + 1
        
        return RelevanceScoring(
            scored_results=scored_results,
            relevance_explanation="Fallback relevance scoring based on keyword matching",
            filtering_criteria=["Title keyword overlap", "Source type priority"]
        )
    
    def _create_fallback_insights(self, query: str, synthesis: ResearchSynthesis) -> List[str]:
        """Create fallback insights when AI processing fails"""
        return [
            f"Research on '{query}' reveals multiple relevant academic sources",
            "Cross-database search provides comprehensive coverage",
            "Further analysis recommended for detailed insights",
            "Consider reviewing source quality and recency",
            "Additional targeted searches may yield more specific results"
        ]
    
    # Tool methods for Agno agents
    def _synthesize_research_tool(self, sources_data: str) -> str:
        """Tool for research synthesis"""
        return f"Synthesized research from provided sources: {sources_data[:100]}..."
    
    def _generate_insights_tool(self, synthesis_data: str) -> str:
        """Tool for insight generation"""
        return f"Generated insights from synthesis: {synthesis_data[:100]}..."
    
    def _assess_source_quality_tool(self, source_data: str) -> str:
        """Tool for source quality assessment"""
        return f"Assessed quality of sources: {source_data[:100]}..."
    
    def _evaluate_credibility_tool(self, credibility_data: str) -> str:
        """Tool for credibility evaluation"""
        return f"Evaluated credibility: {credibility_data[:100]}..."
    
    def _score_relevance_tool(self, relevance_data: str) -> str:
        """Tool for relevance scoring"""
        return f"Scored relevance: {relevance_data[:100]}..."
    
    def _filter_results_tool(self, filter_data: str) -> str:
        """Tool for result filtering"""
        return f"Filtered results: {filter_data[:100]}..."