"""
Incident Store - Memory integration for incident history.

Uses LangGraph Store API to persist incident patterns for future reference.
"""

from typing import List, Dict, Optional
from datetime import datetime
import json

try:
    from langgraph.store.memory import InMemoryStore
except ImportError:
    InMemoryStore = None


class IncidentStore:
    """
    Store for incident history and patterns.
    
    Demonstrates:
    - WRITE pillar: Saving incidents outside conversation context
    - SELECT pillar: Retrieving similar past incidents
    """
    
    def __init__(self):
        """Initialize the incident store."""
        if InMemoryStore is not None:
            self.store = InMemoryStore()
        else:
            # Fallback to simple dict if langgraph store not available
            self.store = {}
            self._use_dict = True
        
        self._use_dict = InMemoryStore is None
        self.namespace = "incidents"
    
    def save_incident(
        self,
        incident_id: str,
        title: str,
        severity: str,
        root_cause: str,
        report: str,
        metadata: Optional[dict] = None
    ) -> None:
        """
        Save a completed incident to the store.
        
        Args:
            incident_id: Unique incident identifier
            title: Incident title
            severity: SEV1-SEV4
            root_cause: Identified root cause
            report: Final postmortem report
            metadata: Additional metadata
        """
        incident_data = {
            "incident_id": incident_id,
            "title": title,
            "severity": severity,
            "root_cause": root_cause,
            "report_summary": report[:500],  # Store summary only
            "created_at": datetime.now().isoformat(),
            "metadata": metadata or {},
        }
        
        if self._use_dict:
            self.store[incident_id] = incident_data
        else:
            self.store.put(
                namespace=(self.namespace,),
                key=incident_id,
                value=incident_data
            )
        
        print(f"✅ Incident {incident_id} saved to store")
    
    def get_incident(self, incident_id: str) -> Optional[dict]:
        """Retrieve a specific incident by ID."""
        if self._use_dict:
            return self.store.get(incident_id)
        else:
            result = self.store.get(
                namespace=(self.namespace,),
                key=incident_id
            )
            return result.value if result else None
    
    def search_similar(
        self,
        query: str,
        limit: int = 5
    ) -> List[dict]:
        """
        Search for similar past incidents.
        
        In production, this would use vector similarity search.
        Here we use simple keyword matching as a demonstration.
        """
        results = []
        query_lower = query.lower()
        keywords = query_lower.split()
        
        if self._use_dict:
            incidents = list(self.store.values())
        else:
            items = self.store.search(namespace=(self.namespace,))
            incidents = [item.value for item in items]
        
        for incident in incidents:
            # Simple relevance scoring
            score = 0
            searchable = f"{incident['title']} {incident['root_cause']}".lower()
            for keyword in keywords:
                if keyword in searchable:
                    score += 1
            
            if score > 0:
                results.append({
                    **incident,
                    "relevance_score": score
                })
        
        # Sort by relevance
        results.sort(key=lambda x: x["relevance_score"], reverse=True)
        return results[:limit]
    
    def get_patterns_by_severity(self, severity: str) -> List[dict]:
        """Get all incidents of a specific severity."""
        if self._use_dict:
            incidents = list(self.store.values())
        else:
            items = self.store.search(namespace=(self.namespace,))
            incidents = [item.value for item in items]
        
        return [i for i in incidents if i["severity"] == severity]
    
    def get_common_root_causes(self, limit: int = 10) -> List[tuple]:
        """Get most common root causes across all incidents."""
        if self._use_dict:
            incidents = list(self.store.values())
        else:
            items = self.store.search(namespace=(self.namespace,))
            incidents = [item.value for item in items]
        
        root_causes = {}
        for incident in incidents:
            rc = incident.get("root_cause", "Unknown")
            # Normalize root cause (simple)
            rc_normalized = rc[:100].lower()
            root_causes[rc_normalized] = root_causes.get(rc_normalized, 0) + 1
        
        sorted_causes = sorted(
            root_causes.items(),
            key=lambda x: x[1],
            reverse=True
        )
        return sorted_causes[:limit]


# Global instance
incident_store = IncidentStore()
