import { useState, useEffect } from 'react';

/**
 * Custom hook for API calls
 * @param {Function} apiFunction - The API function to call
 * @param {Array} dependencies - Dependencies that trigger refetch when changed
 * @param {Array} params - Parameters to pass to the API function
 */
export const useApi = (apiFunction, dependencies = [], params = []) => {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [refetchTrigger, setRefetchTrigger] = useState(0);

  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        setError(null);
        const result = await apiFunction(...params);
        setData(result);
      } catch (err) {
        setError(err.message || 'An error occurred while fetching data');
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [...dependencies, refetchTrigger]);

  const refetch = () => {
    setRefetchTrigger(prev => prev + 1);
  };

  return { data, loading, error, refetch };
};

export default useApi; 