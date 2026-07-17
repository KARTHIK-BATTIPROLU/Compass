"use client";

import { FileText } from "lucide-react";
import ReactMarkdown from "react-markdown";
import { useState } from "react";

interface ArtifactRendererProps {
  content: string;
}

const FlashcardItem = ({ front, back }: { front: string, back: string }) => {
  const [flipped, setFlipped] = useState(false);
  return (
    <div 
      className="relative w-full h-48 cursor-pointer group"
      style={{ perspective: '1000px' }}
      onClick={() => setFlipped(!flipped)}
    >
      <div 
        className={`w-full h-full transition-transform duration-500 ease-in-out`}
        style={{ transformStyle: 'preserve-3d', transform: flipped ? 'rotateY(180deg)' : 'none' }}
      >
        {/* Front */}
        <div 
          className="absolute inset-0 bg-slate-800/90 border border-white/10 rounded-2xl p-6 flex items-center justify-center text-center shadow-lg group-hover:border-white/20 transition-colors"
          style={{ backfaceVisibility: 'hidden' }}
        >
          <p className="text-lg font-medium text-slate-200">{front}</p>
        </div>
        {/* Back */}
        <div 
          className="absolute inset-0 bg-fuchsia-600/90 border border-fuchsia-400/30 rounded-2xl p-6 flex items-center justify-center text-center shadow-lg"
          style={{ backfaceVisibility: 'hidden', transform: 'rotateY(180deg)' }}
        >
          <p className="text-lg font-medium text-white">{back}</p>
        </div>
      </div>
    </div>
  );
};

export function ArtifactRenderer({ content }: ArtifactRendererProps) {
  const scriptRegex = /<artifact type="script">([\s\S]*?)<\/artifact>/;
  const quizRegex = /<artifact type="quiz_link" token="([^"]+)">([\s\S]*?)<\/artifact>/;
  const worksheetRegex = /<artifact type="worksheet">([\s\S]*?)<\/artifact>/;
  const researchBriefRegex = /<artifact type="research_brief">([\s\S]*?)<\/artifact>/;
  const resourceCardRegex = /<artifact type="resource_card">([\s\S]*?)<\/artifact>/;
  const diagramGalleryRegex = /<artifact type="diagram_gallery">([\s\S]*?)<\/artifact>/;
  const flashcardsRegex = /<artifact type="flashcards">([\s\S]*?)<\/artifact>/;
  
  const scriptMatch = content.match(scriptRegex);
  const quizMatch = content.match(quizRegex);
  const worksheetMatch = content.match(worksheetRegex);
  const researchBriefMatch = content.match(researchBriefRegex);
  const resourceCardMatch = content.match(resourceCardRegex);
  const diagramGalleryMatch = content.match(diagramGalleryRegex);
  const flashcardsMatch = content.match(flashcardsRegex);
  
  if (quizMatch) {
    const token = quizMatch[1];
    return (
       <div className="bg-emerald-500/10 border border-emerald-500/20 p-6 rounded-3xl shadow-xl mt-4">
          <h3 className="text-emerald-300 font-bold mb-2 flex items-center gap-2">
            <span className="relative flex h-3 w-3">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
              <span className="relative inline-flex rounded-full h-3 w-3 bg-emerald-500"></span>
            </span>
            Live Quiz Ready!
          </h3>
          <p className="text-sm text-slate-300 mb-4">Share this link with your students. Results will appear here automatically.</p>
          <a href={`/q/${token}`} target="_blank" className="text-emerald-400 underline font-mono bg-black/20 p-2 rounded-lg block w-fit hover:bg-black/40 transition-colors">
            http://localhost:3000/q/{token}
          </a>
       </div>
    );
  }

  if (worksheetMatch) {
    const wsContent = worksheetMatch[1].trim();
    return (
       <div className="bg-blue-500/10 border border-blue-500/20 p-6 rounded-3xl shadow-xl mt-4 relative group">
          <div className="flex justify-between items-center mb-4 border-b border-blue-500/20 pb-4">
            <h3 className="text-blue-300 font-bold flex items-center gap-2">
              <FileText className="w-5 h-5" /> Printable Worksheet
            </h3>
            <button onClick={() => window.print()} className="bg-blue-600 hover:bg-blue-500 text-white px-4 py-2 rounded-xl text-sm font-semibold transition-colors shadow-lg">
              Print to PDF
            </button>
          </div>
          <div className="prose prose-invert prose-blue max-w-none prose-sm print:prose-black print:bg-white print:text-black">
             <ReactMarkdown>{wsContent}</ReactMarkdown>
          </div>
       </div>
    );
  }

  if (researchBriefMatch) {
    try {
      const data = JSON.parse(researchBriefMatch[1].trim());
      return (
        <div className="bg-amber-500/10 border border-amber-500/20 p-6 rounded-3xl shadow-xl mt-4">
          <h3 className="text-amber-300 font-bold mb-4 text-xl flex items-center gap-2">
            Update & Research: {data.title}
          </h3>
          <div className="prose prose-invert prose-amber max-w-none prose-sm mb-6">
            <ReactMarkdown>{data.brief_markdown}</ReactMarkdown>
          </div>
          <div className="border-t border-amber-500/20 pt-4">
            <h4 className="text-amber-400 font-semibold mb-2 text-sm uppercase tracking-wider">Citations</h4>
            <ul className="space-y-2 text-sm text-slate-300">
              {data.citations?.map((c: any, i: number) => (
                <li key={i} className="flex items-start gap-2">
                  <span className="text-amber-500 font-mono">[{c.id}]</span>
                  <a href={c.url} target="_blank" className="hover:text-amber-300 underline underline-offset-2 transition-colors break-all">
                    {c.title}
                  </a>
                </li>
              ))}
            </ul>
          </div>
        </div>
      );
    } catch (e) {
      return <div className="text-red-400 p-4 border border-red-500/20 rounded-xl bg-red-500/10">Error parsing research brief.</div>;
    }
  }

  if (resourceCardMatch) {
    try {
      const data = JSON.parse(resourceCardMatch[1].trim());
      return (
        <div className="bg-cyan-500/10 border border-cyan-500/20 p-6 rounded-3xl shadow-xl mt-4">
          <h3 className="text-cyan-300 font-bold mb-4 text-xl">Resource Card</h3>
          
          <div className="flex gap-2 mb-4 border-b border-cyan-500/20 pb-4 overflow-x-auto">
            <div className="flex-1 bg-black/20 p-3 rounded-xl border border-cyan-500/10">
               <span className="text-cyan-400 font-semibold text-xs uppercase block mb-1">News</span>
               <div className="text-xs text-slate-300 truncate max-w-[150px]">{data.news?.length || 0} items</div>
            </div>
            <div className="flex-1 bg-black/20 p-3 rounded-xl border border-cyan-500/10">
               <span className="text-cyan-400 font-semibold text-xs uppercase block mb-1">Papers</span>
               <div className="text-xs text-slate-300 truncate max-w-[150px]">{data.papers?.length || 0} items</div>
            </div>
            <div className="flex-1 bg-black/20 p-3 rounded-xl border border-cyan-500/10">
               <span className="text-cyan-400 font-semibold text-xs uppercase block mb-1">Docs</span>
               <div className="text-xs text-slate-300 truncate max-w-[150px]">{data.docs?.length || 0} items</div>
            </div>
          </div>

          <div className="prose prose-invert prose-cyan max-w-none prose-sm mb-6">
            <ReactMarkdown>{data.synthesis_markdown}</ReactMarkdown>
          </div>

          <div className="border-t border-cyan-500/20 pt-4">
            <h4 className="text-cyan-400 font-semibold mb-2 text-sm uppercase tracking-wider">Citations</h4>
            <ul className="space-y-2 text-sm text-slate-300">
              {data.citations?.map((c: any, i: number) => (
                <li key={i} className="flex items-start gap-2">
                  <span className="text-cyan-500 font-mono">[{c.id}]</span>
                  <a href={c.url} target="_blank" className="hover:text-cyan-300 underline underline-offset-2 transition-colors break-all">
                    {c.title}
                  </a>
                </li>
              ))}
            </ul>
          </div>
        </div>
      );
    } catch (e) {
      return <div className="text-red-400 p-4 border border-red-500/20 rounded-xl bg-red-500/10">Error parsing resource card.</div>;
    }
  }

  if (diagramGalleryMatch) {
    try {
      const data = JSON.parse(diagramGalleryMatch[1].trim());
      return (
        <div className="bg-pink-500/10 border border-pink-500/20 p-6 rounded-3xl shadow-xl mt-4">
          <h3 className="text-pink-300 font-bold mb-4 text-xl">Diagram Gallery</h3>
          <div className="space-y-6">
            {data.images?.map((img: any, i: number) => (
              <div key={i} className="bg-black/30 rounded-2xl overflow-hidden border border-white/5">
                <img src={img.url} alt={img.title} className="w-full h-auto max-h-64 object-contain bg-slate-950 p-2" />
                <div className="p-4">
                  <a href={img.source_url} target="_blank" className="text-xs text-pink-400 hover:underline block mb-2 font-mono truncate">Source: {img.title}</a>
                  <p className="text-sm text-slate-300">{img.breakdown}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      );
    } catch (e) {
       return <div className="text-red-400 p-4 border border-red-500/20 rounded-xl bg-red-500/10">Error parsing diagram gallery.</div>;
    }
  }

  if (flashcardsMatch) {
    try {
      const data = JSON.parse(flashcardsMatch[1].trim());
      return (
        <div className="bg-fuchsia-500/10 border border-fuchsia-500/20 p-6 rounded-3xl shadow-xl mt-4">
          <h3 className="text-fuchsia-300 font-bold mb-6 text-xl text-center tracking-wide uppercase">Flashcards: {data.title}</h3>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            {data.cards?.map((card: any, i: number) => (
              <FlashcardItem key={i} front={card.front} back={card.back} />
            ))}
          </div>
          <div className="text-center mt-6">
            <span className="text-xs text-fuchsia-400/50 uppercase tracking-widest">Click to flip</span>
          </div>
        </div>
      );
    } catch (e) {
       return <div className="text-red-400 p-4 border border-red-500/20 rounded-xl bg-red-500/10">Error parsing flashcards.</div>;
    }
  }
  
  if (!scriptMatch) {
    return <div className="whitespace-pre-wrap">{content}</div>;
  }

  const beforeText = content.split('<artifact')[0].trim();
  const artifactContent = scriptMatch[1].trim();
  const afterText = content.split('</artifact>')[1]?.trim();

  // Custom parser to split by headers: Introduction, Body, Quiz
  const parseSections = (text: string) => {
    // Split text by markdown headers that start with ##
    // We assume the LLM follows the structure.
    const parts = text.split(/(?=\n## )/g);
    return parts.map(s => s.trim()).filter(Boolean);
  };
  
  const sections = parseSections(artifactContent);

  return (
    <div className="flex flex-col gap-4">
      {beforeText && <div className="whitespace-pre-wrap">{beforeText}</div>}
      
      <div className="bg-white/5 border border-white/10 rounded-3xl overflow-hidden shadow-2xl my-2 backdrop-blur-xl">
        <div className="bg-indigo-600/30 border-b border-white/10 px-5 py-4 flex items-center gap-3">
          <FileText className="w-5 h-5 text-indigo-300" />
          <span className="text-sm font-bold text-indigo-100 tracking-widest uppercase">Generated Lesson Script</span>
        </div>
        <div className="p-2 space-y-2">
          {sections.map((section, idx) => (
            <div key={idx} className="bg-slate-900/40 rounded-2xl p-5 border border-white/5 hover:border-white/20 transition-all duration-300">
              <ReactMarkdown className="prose prose-invert prose-indigo max-w-none prose-headings:mt-0 prose-h2:text-lg prose-h2:text-indigo-200 prose-p:leading-relaxed prose-sm text-slate-300">
                {section}
              </ReactMarkdown>
            </div>
          ))}
        </div>
      </div>
      
      {afterText && <div className="whitespace-pre-wrap">{afterText}</div>}
    </div>
  );
}
