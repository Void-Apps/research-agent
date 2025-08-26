"""
Unit tests for Agno AI service
"""
import pytest
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime

from services.agno_ai_service import (
    AgnoAIService, 
    ResearchSynthesis, 
    QualityAnalysis, 
    RelevanceScoring
)
from models.research import SourceResult, SourceType

class TestAgnoAIService:
    """Test cases for AgnoAIService"""
    
    @pytest.fixture
    def ai_service(self):
        """Create AgnoAIService instance for testing"""
        return AgnoAIService(model_name="gpt-4")
    
    @pytest.fixture
    def sample_source_results(self):
        """Create sample source results for testing"""
        return [
            SourceResult(
                title="Machine Learning in Healthcare",
                authors=["Dr. Smith", "Dr. Johnson"],
                abstract="This paper explores the applications of machine learning in healthcare...",
                url="https://example.com/paper1",
                publication_date=datetime(2023, 1, 15),
                source_type=SourceType.GOOGLE_SCHOLAR,
                citation_count=150
            ),
            SourceResult(
                title="AI Ethics and Healthcare",
                authors=["Prof. Brown"],
                abstract="An examination of ethical considerations in AI healthcare applications...",
                url="https://example.com/paper2",
                publication_date=datetime(2023, 3, 20),
                source_type=SourceType.SCIENCEDIRECT,
                doi="10.1016/j.example.2023.01.001",
                journal="Journal of Medical AI"
            ),
            SourceResult(
                title="Healthcare AI: A Comprehensive Guide",
                authors=["Dr. Wilson", "Dr. Davis"],
                abstract="A comprehensive guide to implementing AI solutions in healthcare settings...",
                url="https://example.com/book1",
                publication_date=datetime(2022, 11, 10),
                source_type=SourceType.GOOGLE_BOOKS,
                isbn="978-0123456789",
                preview_link="https://books.google.com/preview1"
            )
        ]
    
    @pytest.fixture
    def sample_results_by_source(self, sample_source_results):
        """Create sample results organized by source type"""
        return {
            "google_scholar": [sample_source_results[0]],
            "sciencedirect": [sample_source_results[1]],
            "google_books": [sample_source_results[2]]
        }
    
    def test_init(self):
        """Test AgnoAIService initialization"""
        service = AgnoAIService(model_name="gpt-3.5-turbo")
        assert service.model_name == "gpt-3.5-turbo"
        assert service._research_agent is None
        assert service._quality_agent is None
        assert service._relevance_agent is None
    
    def test_init_default_model(self):
        """Test AgnoAIService initialization with default model"""
        service = AgnoAIService()
        assert service.model_name == "gpt-4"
    
    @patch('services.agno_ai_service.Agent')
    @patch('services.agno_ai_service.OpenAIChat')
    def test_get_research_agent(self, mock_openai_chat, mock_agent, ai_service):
        """Test research agent creation"""
        mock_openai_chat.return_value = Mock()
        mock_agent.return_value = Mock()
        
        agent = ai_service._get_research_agent()
        
        assert agent is not None
        assert ai_service._research_agent is agent
        mock_openai_chat.assert_called_once_with(id="gpt-4")
        mock_agent.assert_called_once()
        
        # Test agent reuse
        agent2 = ai_service._get_research_agent()
        assert agent2 is agent
        assert mock_agent.call_count == 1  # Should not create new agent
    
    @patch('services.agno_ai_service.Agent')
    @patch('services.agno_ai_service.OpenAIChat')
    def test_get_quality_agent(self, mock_openai_chat, mock_agent, ai_service):
        """Test quality agent creation"""
        mock_openai_chat.return_value = Mock()
        mock_agent.return_value = Mock()
        
        agent = ai_service._get_quality_agent()
        
        assert agent is not None
        assert ai_service._quality_agent is agent
        mock_openai_chat.assert_called_once_with(id="gpt-4")
        mock_agent.assert_called_once()
    
    @patch('services.agno_ai_service.Agent')
    @patch('services.agno_ai_service.OpenAIChat')
    def test_get_relevance_agent(self, mock_openai_chat, mock_agent, ai_service):
        """Test relevance agent creation"""
        mock_openai_chat.return_value = Mock()
        mock_agent.return_value = Mock()
        
        agent = ai_service._get_relevance_agent()
        
        assert agent is not None
        assert ai_service._relevance_agent is agent
        mock_openai_chat.assert_called_once_with(id="gpt-4")
        mock_agent.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_synthesize_research_results_success(self, ai_service, sample_results_by_source):
        """Test successful research synthesis"""
        mock_agent = AsyncMock()
        mock_response = """
        Summary: This research explores machine learning applications in healthcare with focus on ethics and implementation.
        
        Key Insights:
        - Machine learning shows promise in healthcare applications
        - Ethical considerations are crucial for AI implementation
        - Comprehensive guides are available for practitioners
        
        Confidence Score: 0.85
        
        Methodology: Analyzed findings from academic papers, scientific journals, and comprehensive guides.
        """
        mock_agent.run.return_value = mock_response
        
        with patch.object(ai_service, '_get_research_agent', return_value=mock_agent):
            result = await ai_service.synthesize_research_results(
                "machine learning in healthcare", 
                sample_results_by_source
            )
        
        assert isinstance(result, ResearchSynthesis)
        assert "machine learning applications in healthcare" in result.summary.lower()
        assert len(result.key_insights) >= 3
        assert 0.0 <= result.confidence_score <= 1.0
        assert result.methodology_notes is not None
        mock_agent.run.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_synthesize_research_results_failure(self, ai_service, sample_results_by_source):
        """Test research synthesis with AI failure"""
        mock_agent = AsyncMock()
        mock_agent.run.side_effect = Exception("AI service unavailable")
        
        with patch.object(ai_service, '_get_research_agent', return_value=mock_agent):
            result = await ai_service.synthesize_research_results(
                "machine learning in healthcare", 
                sample_results_by_source
            )
        
        assert isinstance(result, ResearchSynthesis)
        assert "fallback synthesis" in result.methodology_notes.lower()
        assert result.confidence_score == 0.6
        assert len(result.key_insights) >= 1
    
    @pytest.mark.asyncio
    async def test_analyze_research_quality_success(self, ai_service, sample_source_results):
        """Test successful quality analysis"""
        mock_agent = AsyncMock()
        mock_response = """
        Overall Quality Score: 0.82
        
        Credibility Assessment: The sources demonstrate high quality with peer-reviewed publications and reputable authors.
        
        Recommendations:
        - Continue focusing on recent publications
        - Verify author credentials for newer sources
        - Consider impact factor of journals
        """
        mock_agent.run.return_value = mock_response
        
        with patch.object(ai_service, '_get_quality_agent', return_value=mock_agent):
            result = await ai_service.analyze_research_quality(sample_source_results)
        
        assert isinstance(result, QualityAnalysis)
        assert 0.0 <= result.overall_quality_score <= 1.0
        assert "quality" in result.credibility_assessment.lower()
        assert len(result.recommendations) >= 1
        mock_agent.run.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_analyze_research_quality_failure(self, ai_service, sample_source_results):
        """Test quality analysis with AI failure"""
        mock_agent = AsyncMock()
        mock_agent.run.side_effect = Exception("AI service unavailable")
        
        with patch.object(ai_service, '_get_quality_agent', return_value=mock_agent):
            result = await ai_service.analyze_research_quality(sample_source_results)
        
        assert isinstance(result, QualityAnalysis)
        assert result.overall_quality_score == 0.7
        assert "quality analysis completed" in result.credibility_assessment.lower()
        assert len(result.recommendations) >= 1
    
    @pytest.mark.asyncio
    async def test_score_relevance_success(self, ai_service, sample_source_results):
        """Test successful relevance scoring"""
        mock_agent = AsyncMock()
        mock_response = """
        Relevance Scores:
        1. Machine Learning in Healthcare - 0.95
        2. AI Ethics and Healthcare - 0.88
        3. Healthcare AI Guide - 0.92
        
        Methodology: Scored based on semantic relevance and topical alignment.
        """
        mock_agent.run.return_value = mock_response
        
        with patch.object(ai_service, '_get_relevance_agent', return_value=mock_agent):
            result = await ai_service.score_relevance(
                "machine learning healthcare", 
                sample_source_results
            )
        
        assert isinstance(result, RelevanceScoring)
        assert len(result.scored_results) == len(sample_source_results)
        assert all("relevance_score" in item for item in result.scored_results)
        assert all("rank" in item for item in result.scored_results)
        assert result.relevance_explanation is not None
        mock_agent.run.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_score_relevance_failure(self, ai_service, sample_source_results):
        """Test relevance scoring with AI failure"""
        mock_agent = AsyncMock()
        mock_agent.run.side_effect = Exception("AI service unavailable")
        
        with patch.object(ai_service, '_get_relevance_agent', return_value=mock_agent):
            result = await ai_service.score_relevance(
                "machine learning healthcare", 
                sample_source_results
            )
        
        assert isinstance(result, RelevanceScoring)
        assert len(result.scored_results) == len(sample_source_results)
        assert "fallback" in result.relevance_explanation.lower()
        assert len(result.filtering_criteria) >= 1
    
    @pytest.mark.asyncio
    async def test_generate_research_insights_success(self, ai_service):
        """Test successful insights generation"""
        mock_agent = AsyncMock()
        mock_response = """
        Actionable Insights:
        1. Machine learning can significantly improve diagnostic accuracy
        2. Ethical frameworks must be established before implementation
        3. Training programs are needed for healthcare professionals
        4. Data privacy regulations require careful consideration
        5. Cost-benefit analysis should guide adoption decisions
        """
        mock_agent.run.return_value = mock_response
        
        synthesis = ResearchSynthesis(
            summary="Research shows promise for ML in healthcare",
            key_insights=["Diagnostic improvement", "Ethical considerations"],
            confidence_score=0.8
        )
        
        quality_analysis = QualityAnalysis(
            overall_quality_score=0.75,
            source_scores={},
            credibility_assessment="High quality sources",
            recommendations=["Continue research"]
        )
        
        with patch.object(ai_service, '_get_research_agent', return_value=mock_agent):
            result = await ai_service.generate_research_insights(
                "machine learning healthcare", 
                synthesis, 
                quality_analysis
            )
        
        assert isinstance(result, list)
        assert len(result) >= 3
        assert all(isinstance(insight, str) for insight in result)
        mock_agent.run.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_generate_research_insights_failure(self, ai_service):
        """Test insights generation with AI failure"""
        mock_agent = AsyncMock()
        mock_agent.run.side_effect = Exception("AI service unavailable")
        
        synthesis = ResearchSynthesis(
            summary="Research shows promise for ML in healthcare",
            key_insights=["Diagnostic improvement"],
            confidence_score=0.8
        )
        
        quality_analysis = QualityAnalysis(
            overall_quality_score=0.75,
            source_scores={},
            credibility_assessment="High quality sources",
            recommendations=["Continue research"]
        )
        
        with patch.object(ai_service, '_get_research_agent', return_value=mock_agent):
            result = await ai_service.generate_research_insights(
                "machine learning healthcare", 
                synthesis, 
                quality_analysis
            )
        
        assert isinstance(result, list)
        assert len(result) >= 1
        assert all(isinstance(insight, str) for insight in result)
    
    def test_build_synthesis_prompt(self, ai_service, sample_results_by_source):
        """Test synthesis prompt building"""
        prompt = ai_service._build_synthesis_prompt(
            "machine learning in healthcare", 
            sample_results_by_source
        )
        
        assert "machine learning in healthcare" in prompt
        assert "GOOGLE_SCHOLAR RESULTS" in prompt
        assert "SCIENCEDIRECT RESULTS" in prompt
        assert "GOOGLE_BOOKS RESULTS" in prompt
        assert "Machine Learning in Healthcare" in prompt
        assert "comprehensive summary" in prompt.lower()
    
    def test_build_quality_analysis_prompt(self, ai_service, sample_source_results):
        """Test quality analysis prompt building"""
        prompt = ai_service._build_quality_analysis_prompt(sample_source_results)
        
        assert "quality and credibility" in prompt.lower()
        assert "Machine Learning in Healthcare" in prompt
        assert "Dr. Smith" in prompt
        assert "overall quality score" in prompt.lower()
        assert "publication venue" in prompt.lower()
    
    def test_build_relevance_prompt(self, ai_service, sample_source_results):
        """Test relevance scoring prompt building"""
        prompt = ai_service._build_relevance_prompt(
            "machine learning healthcare", 
            sample_source_results
        )
        
        assert "machine learning healthcare" in prompt
        assert "relevance of these research results" in prompt.lower()
        assert "Machine Learning in Healthcare" in prompt
        assert "relevance scores" in prompt.lower()
        assert "semantic relevance" in prompt.lower()
    
    def test_build_insights_prompt(self, ai_service):
        """Test insights generation prompt building"""
        synthesis = ResearchSynthesis(
            summary="ML shows promise in healthcare",
            key_insights=["Diagnostic accuracy", "Cost reduction"],
            confidence_score=0.8
        )
        
        quality_analysis = QualityAnalysis(
            overall_quality_score=0.75,
            source_scores={},
            credibility_assessment="High quality research",
            recommendations=["Continue studies"]
        )
        
        prompt = ai_service._build_insights_prompt(
            "machine learning healthcare", 
            synthesis, 
            quality_analysis
        )
        
        assert "machine learning healthcare" in prompt
        assert "ML shows promise in healthcare" in prompt
        assert "Diagnostic accuracy" in prompt
        assert "High quality research" in prompt
        assert "actionable insights" in prompt.lower()
    
    def test_parse_synthesis_response(self, ai_service):
        """Test parsing of synthesis response"""
        response = """
        Summary: This is a comprehensive research summary about machine learning in healthcare.
        
        Key Insights:
        - Machine learning improves diagnostic accuracy
        - Cost reduction is a major benefit
        - Training is required for implementation
        
        Confidence Score: 0.85
        
        Methodology Notes: Used systematic analysis of multiple sources.
        """
        
        result = ai_service._parse_synthesis_response(response)
        
        assert isinstance(result, ResearchSynthesis)
        assert "comprehensive research summary" in result.summary
        assert len(result.key_insights) == 3
        assert result.confidence_score == 0.85
        assert "systematic analysis" in result.methodology_notes
    
    def test_parse_quality_response(self, ai_service):
        """Test parsing of quality analysis response"""
        response = """
        Overall Quality Score: 0.78
        
        Credibility Assessment: The sources demonstrate good quality with peer-reviewed content.
        
        Recommendations:
        - Verify recent publications
        - Check author credentials
        - Review journal impact factors
        """
        
        result = ai_service._parse_quality_response(response)
        
        assert isinstance(result, QualityAnalysis)
        assert result.overall_quality_score == 0.78
        assert "peer-reviewed content" in result.credibility_assessment
        assert len(result.recommendations) == 3
        assert "Verify recent publications" in result.recommendations[0]
    
    def test_parse_relevance_response(self, ai_service, sample_source_results):
        """Test parsing of relevance scoring response"""
        response = """
        Relevance Scores:
        1. Result 1 - 0.95
        2. Result 2 - 0.88
        3. Result 3 - 0.92
        """
        
        result = ai_service._parse_relevance_response(response, sample_source_results)
        
        assert isinstance(result, RelevanceScoring)
        assert len(result.scored_results) == len(sample_source_results)
        assert all("relevance_score" in item for item in result.scored_results)
        assert all("rank" in item for item in result.scored_results)
        assert result.relevance_explanation is not None
    
    def test_parse_insights_response(self, ai_service):
        """Test parsing of insights response"""
        response = """
        1. Machine learning can improve diagnostic accuracy by 25%
        2. Implementation requires significant training investment
        3. Ethical guidelines must be established first
        - Cost-benefit analysis shows positive ROI
        • Patient privacy concerns need addressing
        """
        
        result = ai_service._parse_insights_response(response)
        
        assert isinstance(result, list)
        assert len(result) == 5
        assert "diagnostic accuracy by 25%" in result[0]
        assert "training investment" in result[1]
        assert "ethical guidelines" in result[2].lower()
    
    def test_create_fallback_synthesis(self, ai_service, sample_results_by_source):
        """Test fallback synthesis creation"""
        result = ai_service._create_fallback_synthesis(
            "machine learning healthcare", 
            sample_results_by_source
        )
        
        assert isinstance(result, ResearchSynthesis)
        assert "machine learning healthcare" in result.summary
        assert "3 relevant sources" in result.summary
        assert "3 databases" in result.summary
        assert result.confidence_score == 0.6
        assert "fallback synthesis" in result.methodology_notes.lower()
    
    def test_create_fallback_quality_analysis(self, ai_service, sample_source_results):
        """Test fallback quality analysis creation"""
        result = ai_service._create_fallback_quality_analysis(sample_source_results)
        
        assert isinstance(result, QualityAnalysis)
        assert result.overall_quality_score == 0.7
        assert f"{len(sample_source_results)} sources" in result.credibility_assessment
        assert len(result.recommendations) >= 3
    
    def test_create_fallback_relevance_scoring(self, ai_service, sample_source_results):
        """Test fallback relevance scoring creation"""
        result = ai_service._create_fallback_relevance_scoring(
            "machine learning healthcare", 
            sample_source_results
        )
        
        assert isinstance(result, RelevanceScoring)
        assert len(result.scored_results) == len(sample_source_results)
        assert "fallback" in result.relevance_explanation.lower()
        assert len(result.filtering_criteria) >= 2
        
        # Check that results are properly scored and ranked
        for item in result.scored_results:
            assert "relevance_score" in item
            assert "rank" in item
            assert 0.0 <= item["relevance_score"] <= 1.0
    
    def test_create_fallback_insights(self, ai_service):
        """Test fallback insights creation"""
        synthesis = ResearchSynthesis(
            summary="Test summary",
            key_insights=["Test insight"],
            confidence_score=0.8
        )
        
        result = ai_service._create_fallback_insights("test query", synthesis)
        
        assert isinstance(result, list)
        assert len(result) >= 5
        assert all(isinstance(insight, str) for insight in result)
        assert "test query" in result[0].lower()
    
    def test_tool_methods(self, ai_service):
        """Test tool methods for Agno agents"""
        # Test synthesis tool
        result = ai_service._synthesize_research_tool("test data")
        assert "Synthesized research" in result
        assert "test data" in result
        
        # Test insights tool
        result = ai_service._generate_insights_tool("test synthesis")
        assert "Generated insights" in result
        assert "test synthesis" in result
        
        # Test quality assessment tool
        result = ai_service._assess_source_quality_tool("test source")
        assert "Assessed quality" in result
        assert "test source" in result
        
        # Test credibility evaluation tool
        result = ai_service._evaluate_credibility_tool("test credibility")
        assert "Evaluated credibility" in result
        assert "test credibility" in result
        
        # Test relevance scoring tool
        result = ai_service._score_relevance_tool("test relevance")
        assert "Scored relevance" in result
        assert "test relevance" in result
        
        # Test filtering tool
        result = ai_service._filter_results_tool("test filter")
        assert "Filtered results" in result
        assert "test filter" in result

class TestResearchSynthesis:
    """Test cases for ResearchSynthesis model"""
    
    def test_init(self):
        """Test ResearchSynthesis initialization"""
        synthesis = ResearchSynthesis(
            summary="Test summary",
            key_insights=["Insight 1", "Insight 2"],
            confidence_score=0.85,
            methodology_notes="Test methodology"
        )
        
        assert synthesis.summary == "Test summary"
        assert synthesis.key_insights == ["Insight 1", "Insight 2"]
        assert synthesis.confidence_score == 0.85
        assert synthesis.methodology_notes == "Test methodology"
    
    def test_init_optional_methodology(self):
        """Test ResearchSynthesis initialization without methodology notes"""
        synthesis = ResearchSynthesis(
            summary="Test summary",
            key_insights=["Insight 1"],
            confidence_score=0.75
        )
        
        assert synthesis.summary == "Test summary"
        assert synthesis.key_insights == ["Insight 1"]
        assert synthesis.confidence_score == 0.75
        assert synthesis.methodology_notes is None

class TestQualityAnalysis:
    """Test cases for QualityAnalysis model"""
    
    def test_init(self):
        """Test QualityAnalysis initialization"""
        analysis = QualityAnalysis(
            overall_quality_score=0.8,
            source_scores={"source1": 0.9, "source2": 0.7},
            credibility_assessment="High quality sources",
            recommendations=["Rec 1", "Rec 2"]
        )
        
        assert analysis.overall_quality_score == 0.8
        assert analysis.source_scores == {"source1": 0.9, "source2": 0.7}
        assert analysis.credibility_assessment == "High quality sources"
        assert analysis.recommendations == ["Rec 1", "Rec 2"]

class TestRelevanceScoring:
    """Test cases for RelevanceScoring model"""
    
    def test_init(self):
        """Test RelevanceScoring initialization"""
        scored_results = [
            {"result": "test1", "score": 0.9, "rank": 1},
            {"result": "test2", "score": 0.7, "rank": 2}
        ]
        
        scoring = RelevanceScoring(
            scored_results=scored_results,
            relevance_explanation="Test explanation",
            filtering_criteria=["Criteria 1", "Criteria 2"]
        )
        
        assert scoring.scored_results == scored_results
        assert scoring.relevance_explanation == "Test explanation"
        assert scoring.filtering_criteria == ["Criteria 1", "Criteria 2"]