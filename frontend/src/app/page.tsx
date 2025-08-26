'use client';

import { useRouter } from 'next/navigation';
import { toast } from 'react-hot-toast';
import MainLayout from '@/components/layout/MainLayout';
import ResearchForm from '@/components/ResearchForm';
import { useSubmitResearch } from '@/hooks/useResearch';

export default function Home() {
  const router = useRouter();
  const submitResearchMutation = useSubmitResearch();

  const handleResearchSubmit = async (query: string) => {
    try {
      const result = await submitResearchMutation.mutateAsync({ query });
      toast.success('Research query submitted successfully!');
      // Navigate to results page with the query ID
      router.push(`/results/${result.id}`);
    } catch (error) {
      console.error('Failed to submit research query:', error);
      toast.error('Failed to submit research query. Please try again.');
    }
  };

  return (
    <MainLayout>
      <div className="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
        <div className="px-4 py-6 sm:px-0">
          <div className="text-center mb-8">
            <h1 className="text-4xl font-bold text-gray-900 mb-4">
              AI Research Agent
            </h1>
            <p className="text-xl text-gray-600 max-w-3xl mx-auto">
              Submit your research requirements and get comprehensive findings from 
              Google Scholar, Google Books, and ScienceDirect, all powered by AI.
            </p>
          </div>
          
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-8">
            <ResearchForm 
              onSubmit={handleResearchSubmit} 
              isLoading={submitResearchMutation.isPending}
            />
          </div>
        </div>
      </div>
    </MainLayout>
  );
}