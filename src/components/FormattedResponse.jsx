// src/components/FormattedResponse.jsx
import React, { useState, useEffect } from "react";
import "./FormattedResponse.css";

// --- 1. The Helper Function to Parse Text Tables ---
const parseTextTable = (text) => {
  if (!text) return null;

  // Split by new lines
  const lines = text.split('\n');
  
  // Find lines that look like table rows (must have a pipe '|')
  // We also filter out the separator lines (e.g., "----+-----")
  const tableLines = lines.filter(line => 
    line.includes('|') && !line.match(/^[-\+\s\|]+$/)
  );

  if (tableLines.length < 2) return null; // We need at least a header and one row

  // The first valid line is the header
  const headers = tableLines[0]
    .split('|')
    .map(h => h.trim())
    .filter(h => h); // Remove empty strings

  // The rest are data rows
  const data = tableLines.slice(1).map(line => {
    const values = line.split('|').map(v => v.trim());
    const rowObj = {};
    headers.forEach((header, index) => {
      // Clean up headers like "Treatment History Diagnosis Date" -> "Diagnosis Date"
      // This is specific to your screenshot where the title is merged with the first header
      let cleanHeader = header;
      if (index === 0 && header.includes('Treatment History')) {
         cleanHeader = header.replace('Treatment History', '').trim();
      }
      
      rowObj[cleanHeader] = values[index] || "";
    });
    return rowObj;
  });

  return data;
};

const downloadCSV = (data) => {
  if (!data || data.length === 0) return;
  const headers = Object.keys(data[0]);
  const csvContent =
    headers.join(",") +
    "\n" +
    data.map((row) => headers.map(header => `"${row[header]}"`).join(",")).join("\n");
    
  const blob = new Blob([csvContent], { type: "text/csv" });
  const link = document.createElement("a");
  link.href = URL.createObjectURL(blob);
  link.download = "medical_records.csv";
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
};

const FormattedResponse = ({ formattedResponse, content }) => {
  const [expanded, setExpanded] = useState(true);
  const [tableData, setTableData] = useState(null);

  useEffect(() => {
    // Strategy 1: Use structured JSON if backend sent it
    if (formattedResponse && Array.isArray(formattedResponse) && formattedResponse.length > 0) {
      setTableData(formattedResponse);
    } 
    // Strategy 2: Parse the text content if JSON is missing
    else if (content) {
      const parsed = parseTextTable(content);
      if (parsed) setTableData(parsed);
    }
  }, [formattedResponse, content]);

  // If no data found via either method, don't render anything
  if (!tableData) return null;

  const headers = Object.keys(tableData[0]);

  return (
    <div className="formatted-response">
      <div className="report-header">
        <h3 style={{ margin: 0, fontSize: '1rem', color: '#0056b3' }}>
          <i className="fa-solid fa-table-list" style={{ marginRight: '8px' }}></i>
          Medical Record
        </h3>
        <div className="action-buttons">
          <button className="action-btn" onClick={() => setExpanded(!expanded)}>
            {expanded ? "Hide" : "View"}
          </button>
          <button className="action-btn download" onClick={() => downloadCSV(tableData)}>
            <i className="fa-solid fa-download" style={{ marginRight: '5px' }}></i>
            CSV
          </button>
        </div>
      </div>

      {expanded && (
        <div className="table-wrapper">
          <table className="styled-table">
            <thead>
              <tr>
                {headers.map((h, i) => (
                  <th key={i}>{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {tableData.map((row, i) => (
                <tr key={i}>
                  {headers.map((header, j) => (
                    <td key={j}>
                      {header.toLowerCase().includes('status') ? (
                        <span className={`status-badge ${row[header]?.toLowerCase()}`}>
                          {row[header]}
                        </span>
                      ) : (
                        row[header]
                      )}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
};

export default FormattedResponse;