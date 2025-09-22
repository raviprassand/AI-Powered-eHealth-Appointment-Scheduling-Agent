import React from 'react';
import ReactMarkdown from 'react-markdown';
import './TableModal.css';

const TableModal = ({ isOpen, onClose, tableData, columns, explanation, summary, dataSource }) => {
  if (!isOpen) return null;
  
  console.log("TableModal - tableData:", tableData);
  console.log("TableModal - columns:", columns);
  console.log("TableModal - dataSource:", dataSource);
  
  // Extract table name from dataSource or use a default
  const getTableTitle = () => {
    if (dataSource) {
      // Extract table name from strings like "Tables: patients_treatment" or "patients_treatment table"
      const tableMatch = dataSource.match(/(\w+_?\w+)/);
      if (tableMatch) {
        const tableName = tableMatch[1];
        // Convert snake_case to Title Case
        return tableName
          .split('_')
          .map(word => word.charAt(0).toUpperCase() + word.slice(1))
          .join(' ');
      }
    }
    return 'Database Records';
  };
  
  // Format column names to be more readable
  const formatColumnName = (columnName) => {
    return columnName
      .split('_')
      .map(word => word.charAt(0).toUpperCase() + word.slice(1))
      .join(' ');
  };
  
  // Format values for better display
  const formatValue = (value) => {
    if (value === null || value === undefined || value === '') {
      return 'N/A';
    }
    
    // Handle dates
    if (typeof value === 'string' && value.match(/^\d{4}-\d{2}-\d{2}/)) {
      const date = new Date(value);
      return date.toLocaleDateString('en-US', { 
        year: 'numeric', 
        month: 'long', 
        day: 'numeric' 
      });
    }
    
    // Handle long text
    if (typeof value === 'string' && value.length > 100) {
      return (
        <div className="long-text">
          <div className="text-preview">{value.substring(0, 100)}...</div>
          <details className="text-expandable">
            <summary>Show full text</summary>
            <div className="full-text">{value}</div>
          </details>
        </div>
      );
    }
    
    return String(value);
  };
  
  // Get record type name for individual cards
  const getRecordName = (index) => {
    const tableName = getTableTitle();
    if (tableName.toLowerCase().includes('treatment')) return `Treatment Record ${index + 1}`;
    if (tableName.toLowerCase().includes('patient')) return `Patient Record ${index + 1}`;
    if (tableName.toLowerCase().includes('pathology')) return `Pathology Record ${index + 1}`;
    return `Record ${index + 1}`;
  };
  
  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content" onClick={e => e.stopPropagation()}>
        <button className="close-button" onClick={onClose}>×</button>
        
        <div className="modal-header">
          <h2>{getTableTitle()}</h2>
          {summary && (
            <p className="modal-summary">{summary}</p>
          )}
          {dataSource && (
            <div className="data-source-info">
              <span className="source-label">Source:</span> {dataSource}
            </div>
          )}
        </div>
        
        <div className="modal-patient-container">
          {Array.isArray(tableData) ? (
            <div className="patient-cards">
              {tableData.map((record, recordIndex) => (
                <div key={recordIndex} className="patient-card">
                  <div className="patient-header">
                    <h3>{getRecordName(recordIndex)}</h3>
                    {record.patient_id && (
                      <span className="patient-id">Patient ID: {record.patient_id}</span>
                    )}
                    {record.id && !record.patient_id && (
                      <span className="record-id">ID: {record.id}</span>
                    )}
                  </div>
                  <div className="patient-details">
                    {columns?.map((column, colIndex) => (
                      <div key={colIndex} className="detail-row">
                        <div className="detail-label">
                          <span className="label-text">{formatColumnName(column)}</span>
                          <span className="label-colon">:</span>
                        </div>
                        <div className="detail-value">
                          {formatValue(record[column])}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="patient-card">
              <div className="patient-header">
                <h3>{getTableTitle()}</h3>
              </div>
              <div className="patient-details">
                {Object.entries(tableData).map(([key, value], index) => (
                  <div key={index} className="detail-row">
                    <div className="detail-label">
                      <span className="label-text">{formatColumnName(key)}</span>
                      <span className="label-colon">:</span>
                    </div>
                    <div className="detail-value">
                      {formatValue(value)}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
        
        {explanation && (
          <div className="modal-explanation">
            <h4>Clinical Context</h4>
            <ReactMarkdown>{explanation}</ReactMarkdown>
          </div>
        )}
      </div>
    </div>
  );
};

export default TableModal;