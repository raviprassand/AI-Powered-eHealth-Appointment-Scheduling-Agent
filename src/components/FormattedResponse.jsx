// src/components/FormattedResponse.jsx
import React, { useState } from 'react';
import ReactMarkdown from 'react-markdown';
import TableModal from './TableModal';
import './FormattedResponse.css';

const TableDisplay = ({ tableData, explanation, columns, summary, dataSource, recordCount, keyInsights }) => {
  const [isModalOpen, setIsModalOpen] = useState(false);
  
  try {
    let processedData = {};
    let finalColumns = [];
    
    // Check if tableData is an array of objects (new format)
    if (Array.isArray(tableData)) {
      processedData = tableData;
      finalColumns = columns || Object.keys(processedData[0] || {});
      
      console.log("TableDisplay - Array data:", processedData);
      console.log("TableDisplay - Columns:", finalColumns);
      
      // Display summary first, then option to view full table
      return (
        <div className="formatted-response">
          {/* Summary Section */}
          <div className="summary-section">
            <div className="summary-content">
              <h4>📊 Data Summary</h4>
              <p className="summary-text">{summary}</p>
              
              {dataSource && (
                <div className="data-source">
                  <strong>Source:</strong> {dataSource}
                </div>
              )}
              
              {recordCount && (
                <div className="record-count">
                  <strong>Records Found:</strong> {recordCount}
                </div>
              )}
              
              {keyInsights && keyInsights.length > 0 && (
                <div className="key-insights">
                  <strong>Key Findings:</strong>
                  <ul>
                    {keyInsights.map((insight, index) => (
                      <li key={index}>{insight}</li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
            
            {/* Action Buttons */}
            <div className="action-buttons">
              <button 
                className="view-full-table-btn primary" 
                onClick={() => setIsModalOpen(true)}
              >
                📋 View Full Results
              </button>
            </div>
          </div>
          
          {/* Optional: Small Preview Table (first 3 rows) */}
          {processedData.length > 0 && (
            <div className="preview-section">
              <h5>Preview (showing first 3 records):</h5>
              <div className="preview-table">
                <table>
                  <thead>
                    <tr>
                      {finalColumns.slice(0, 3).map((column, index) => (
                        <th key={index}>{column}</th>
                      ))}
                      {finalColumns.length > 3 && <th>...</th>}
                    </tr>
                  </thead>
                  <tbody>
                    {processedData.slice(0, 3).map((row, rowIndex) => (
                      <tr key={rowIndex}>
                        {finalColumns.slice(0, 3).map((column, cellIndex) => (
                          <td key={cellIndex}>{String(row[column] || 'N/A')}</td>
                        ))}
                        {finalColumns.length > 3 && <td>...</td>}
                      </tr>
                    ))}
                  </tbody>
                </table>
                {processedData.length > 3 && (
                  <p className="more-records">... and {processedData.length - 3} more records</p>
                )}
              </div>
            </div>
          )}
          
          {explanation && (
            <div className="explanation">
              <h4>Clinical Context</h4>
              <ReactMarkdown>{explanation}</ReactMarkdown>
            </div>
          )}
          
          <TableModal 
            isOpen={isModalOpen} 
            onClose={() => setIsModalOpen(false)} 
            tableData={processedData}
            columns={finalColumns}
            explanation={explanation}
            summary={summary}
          />
        </div>
      );
    }
    
    // Existing code for other data types...
    
  } catch (error) {
    console.error("Error parsing table data:", error);
    return <div className="error">Error displaying formatted data</div>;
  }
};

// Update the main component to handle new fields
const FormattedResponse = ({ response }) => {
  if (!response) {
    return <ReactMarkdown>{''}</ReactMarkdown>;
  }
  
  if (response.type === "text") {
      <div className="text-response">
        <ReactMarkdown>{response.content || ''}</ReactMarkdown>
      </div>
  }

  // Handle no_data responses
  if (response.type === "no_data") {
    return (
      <div className="no-data-response">
        <div className="summary-section">
          <h4>🔍 Search Results</h4>
          <p className="summary-text">{response.summary}</p>
          
          {response.data_source && (
            <div className="data-source">
              <strong>Tables Searched:</strong> {response.data_source}
            </div>
          )}
          
          {response.key_insights && response.key_insights.length > 0 && (
            <div className="key-insights">
              <strong>Suggestions:</strong>
              <ul>
                {response.key_insights.map((insight, index) => (
                  <li key={index}>{insight}</li>
                ))}
              </ul>
            </div>
          )}
          
          {response.explanation && (
            <div className="explanation">
              <p>{response.explanation}</p>
            </div>
          )}
        </div>
      </div>
    );
  }
  
  if (response.type === "table" || response.type === "table_data") {
    return <TableDisplay 
      tableData={response.data} 
      columns={response.columns} 
      explanation={response.explanation}
      summary={response.summary}
      dataSource={response.data_source}
      recordCount={response.record_count}
      keyInsights={response.key_insights}
    />;
  }
  
  // If HTML content is available, use it
  if (response.html) {
    return (
      <div className="html-table-container" 
           dangerouslySetInnerHTML={{ __html: response.html }} />
    );
  }
  
  return <ReactMarkdown>{response.content || ''}</ReactMarkdown>;
};

export default FormattedResponse;