import React, { useState, useEffect } from "react";
import FileUpload from "../Settings/FileUpload";
import ToneSelector from "../Settings/ToneSelector";
import MCPSelector from "../Settings/MCPSelector";
import LayoutSelector from "../Settings/LayoutSelector";
import DomainFilter from "./DomainFilter";
import { useAnalytics } from "../../hooks/useAnalytics";
import { ChatBoxSettings, Domain, MCPConfig } from '@/types/data';

interface ResearchFormProps {
  chatBoxSettings: ChatBoxSettings;
  setChatBoxSettings: React.Dispatch<React.SetStateAction<ChatBoxSettings>>;
  onFormSubmit?: (
    task: string,
    reportType: string,
    reportSource: string,
    domains: Domain[]
  ) => void;
}

export default function ResearchForm({
  chatBoxSettings,
  setChatBoxSettings,
  onFormSubmit,
}: ResearchFormProps) {
  const { trackResearchQuery } = useAnalytics();
  const [task, setTask] = useState("");
  const [newDomain, setNewDomain] = useState('');

  // Destructure necessary fields from chatBoxSettings
  let { report_type, report_source, tone, layoutType } = chatBoxSettings;

  const [domains, setDomains] = useState<Domain[]>(() => {
    if (typeof window !== 'undefined') {
      const saved = localStorage.getItem('domainFilters');
      return saved ? JSON.parse(saved) : [];
    }
    return [];
  });
  
  useEffect(() => {
    localStorage.setItem('domainFilters', JSON.stringify(domains));
    setChatBoxSettings(prev => ({
      ...prev,
      domains: domains.map(domain => domain.value)
    }));
  }, [domains, setChatBoxSettings]);

  const handleAddDomain = (e: React.FormEvent) => {
    e.preventDefault();
    if (newDomain.trim()) {
      setDomains([...domains, { value: newDomain.trim() }]);
      setNewDomain('');
    }
  };

  const handleRemoveDomain = (domainToRemove: string) => {
    setDomains(domains.filter(domain => domain.value !== domainToRemove));
  };

  const onFormChange = (e: { target: { name: any; value: any } }) => {
    const { name, value } = e.target;
    setChatBoxSettings((prevSettings: any) => ({
      ...prevSettings,
      [name]: value,
    }));
  };

  const onToneChange = (e: { target: { value: any } }) => {
    const { value } = e.target;
    setChatBoxSettings((prevSettings: any) => ({
      ...prevSettings,
      tone: value,
    }));
  };

  const onLayoutChange = (e: { target: { value: any } }) => {
    const { value } = e.target;
    setChatBoxSettings((prevSettings: any) => ({
      ...prevSettings,
      layoutType: value,
    }));
  };

  const onMCPChange = (enabled: boolean, configs: MCPConfig[]) => {
    setChatBoxSettings((prevSettings: any) => ({
      ...prevSettings,
      mcp_enabled: enabled,
      mcp_configs: configs,
    }));
  };

  const onAcademicModeToggle = (enabled: boolean) => {
    setChatBoxSettings((prevSettings: any) => ({
      ...prevSettings,
      academic_mode: enabled,
      academic_config: prevSettings.academic_config || {
        sources: ["arxiv", "semantic_scholar", "openalex", "core"],
        year_from: null,
        year_to: null,
        oa_only: true,
        max_papers: 12,
        summarize_long_paper: true,
      },
    }));
  };

  const updateAcademicConfig = (patch: Record<string, any>) => {
    setChatBoxSettings((prevSettings: any) => ({
      ...prevSettings,
      academic_config: {
        ...(prevSettings.academic_config || {
          sources: ["arxiv", "semantic_scholar", "openalex", "core"],
          year_from: null,
          year_to: null,
          oa_only: true,
          max_papers: 12,
          summarize_long_paper: true,
        }),
        ...patch,
      },
    }));
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (onFormSubmit) {
      const updatedSettings = {
        ...chatBoxSettings,
        domains: domains.map(domain => domain.value)
      };
      setChatBoxSettings(updatedSettings);
      onFormSubmit(task, report_type, report_source, domains);
    }
  };

  return (
    <form
      method="POST"
      className="report_settings_static mt-3"
      onSubmit={handleSubmit}
    >
      <div className="form-group">
        <label htmlFor="report_type" className="agent_question">
          Report Type{" "}
        </label>
        <select
          name="report_type"
          value={report_type}
          onChange={onFormChange}
          className="form-control-static"
          required
        >
          <option value="research_report">
            Summary - Short and fast (~2 min)
          </option>
          <option value="deep">Deep Research Report</option>
          <option value="multi_agents">Multi Agents Report</option>
          <option value="detailed_report">
            Detailed - In depth and longer (~5 min)
          </option>
        </select>
      </div>

      <div className="form-group">
        <label htmlFor="report_source" className="agent_question">
          Report Source{" "}
        </label>
        <select
          name="report_source"
          value={report_source}
          onChange={onFormChange}
          className="form-control-static"
          required
        >
          <option value="web">The Internet</option>
          <option value="local">My Documents</option>
          <option value="hybrid">Hybrid</option>
        </select>
      </div>

      

      {report_source === "local" || report_source === "hybrid" ? (
        <FileUpload />
      ) : null}
      
      <ToneSelector tone={tone} onToneChange={onToneChange} />

      <MCPSelector 
        mcpEnabled={chatBoxSettings.mcp_enabled || false}
        mcpConfigs={chatBoxSettings.mcp_configs || []}
        onMCPChange={onMCPChange}
      />

      <div className="form-group academic-mode-group">
        <label className="agent_question">
          <input
            type="checkbox"
            checked={chatBoxSettings.academic_mode || false}
            onChange={(e) => onAcademicModeToggle(e.target.checked)}
            style={{ marginRight: 8 }}
          />
          Academic Research Mode (Communications)
        </label>
        {chatBoxSettings.academic_mode && (
          <div className="academic-config-grid" style={{ marginTop: 8 }}>
            <label htmlFor="academic_sources">Academic Sources</label>
            <input
              id="academic_sources"
              className="form-control-static"
              value={(chatBoxSettings.academic_config?.sources || []).join(",")}
              onChange={(e) => {
                const sources = e.target.value
                  .split(",")
                  .map((s) => s.trim())
                  .filter(Boolean);
                updateAcademicConfig({ sources });
              }}
            />
            <label htmlFor="academic_year_from">Year From</label>
            <input
              id="academic_year_from"
              type="number"
              className="form-control-static"
              value={chatBoxSettings.academic_config?.year_from ?? ""}
              onChange={(e) => updateAcademicConfig({ year_from: e.target.value ? Number(e.target.value) : null })}
            />
            <label htmlFor="academic_year_to">Year To</label>
            <input
              id="academic_year_to"
              type="number"
              className="form-control-static"
              value={chatBoxSettings.academic_config?.year_to ?? ""}
              onChange={(e) => updateAcademicConfig({ year_to: e.target.value ? Number(e.target.value) : null })}
            />
            <label htmlFor="academic_max_papers">Max Papers</label>
            <input
              id="academic_max_papers"
              type="number"
              min={1}
              max={50}
              className="form-control-static"
              value={chatBoxSettings.academic_config?.max_papers ?? 12}
              onChange={(e) => updateAcademicConfig({ max_papers: Number(e.target.value || 12) })}
            />
            <label className="agent_question">
              <input
                type="checkbox"
                checked={chatBoxSettings.academic_config?.oa_only ?? true}
                onChange={(e) => updateAcademicConfig({ oa_only: e.target.checked })}
                style={{ marginRight: 8 }}
              />
              OA only
            </label>
            <label className="agent_question">
              <input
                type="checkbox"
                checked={chatBoxSettings.academic_config?.summarize_long_paper ?? true}
                onChange={(e) => updateAcademicConfig({ summarize_long_paper: e.target.checked })}
                style={{ marginRight: 8 }}
              />
              Summarize long papers
            </label>
          </div>
        )}
      </div>
      
      <LayoutSelector layoutType={layoutType || 'copilot'} onLayoutChange={onLayoutChange} />

      {/** TODO: move the below to its own component */}
      {(chatBoxSettings.report_source === "web" || chatBoxSettings.report_source === "hybrid") && (
        <DomainFilter
          domains={domains}
          newDomain={newDomain}
          setNewDomain={setNewDomain}
          onAddDomain={handleAddDomain}
          onRemoveDomain={handleRemoveDomain}
        />
      )}
    </form>
  );
}
