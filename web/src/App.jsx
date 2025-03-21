import { useMemo, useState } from "react";
import { Index } from "lunr";
import "./App.css";

import rawIndex from "./assets/index.json";
import companies from "./assets/everything.json";

function App() {
  const idx = useMemo(() => Index.load(rawIndex), []);
  const [search, setSearch] = useState("");

  const companiesByDetail = useMemo(() => {
    const map = new Map();
    companies.forEach((company) => {
      map.set(company.detail_url, company);
    });
    return map;
  }, []);

  const results = useMemo(() => {
    if (!search) {
      return null;
    }
    try {
      return idx.search(search);
    } catch {
      return []
    }
  }, [idx, search]);

  const filteredCompanies = useMemo(() => {
    if (!results) {
      return companies
    }
    return results.map((result) => {
      const ref = result.ref;
      return companiesByDetail.get(ref);
    });
  }, [results, companiesByDetail]);

  const matches = useMemo(() => {
    const matches = new Map();
    
    if (!results) return matches;

    results.forEach((result) => {
      const ref = result.ref;
      const metadata = result.matchData.metadata;

      Object.entries(metadata).forEach(([term, fields]) => {
        Object.entries(fields).forEach(([field, { position }]) => {
          position.forEach(([start, length]) => {
            const refMatches = matches.get(ref) ?? [];
            refMatches.push({
              ref,
              term,
              field,
              pos: [start, length],
            });
            matches.set(ref, refMatches);
          });
        });
      });
    });

    return matches;
  }, [results]);

  return (
    <>
      <div className="p-1">
        <div className="mb-3 w-full text-center p-3">
          <input
            onChange={(e) => setSearch(e.target.value)}
            className="border w-full max-w-[600px] h-8 text-lg px-1"
          />
        </div>
        <div className="space-y-2">
          {filteredCompanies.length ===0 && (<>No results found.</>)}
          {filteredCompanies.map((company) => {
            return (
              <Company
                key={company.detail_url}
                company={company}
                matches={matches.get(company.detail_url) ?? []}
              />
            );
          })}
        </div>
      </div>
    </>
  );
}

/** Return a list of spans where terms that are mathed in the value are highlighted. */
// TOOD(joeriddles): this could also be a component instead of a hook
function useMatch(matches, field, value) {
  return useMemo(() => {
    if (!value) {
      return <></>;
    }

    const filteredMatches = matches.filter((match) => match.field === field);
    if (filteredMatches) {
      let prevIndex = 0;
      const spans = filteredMatches.map((match) => {
        const { pos } = match;
        const [start, length] = pos;
        const endIndex = start + length;
        const left = value.substring(prevIndex, start);
        const matching = value.substring(start, endIndex);
        prevIndex = endIndex;
        return (
          <span key={`${pos}`}>
            {left}
            <span className="bg-amber-300 rounded">{matching}</span>
          </span>
        );
      });
      spans.push(<span key="end">{value.substring(prevIndex)}</span>);
      return spans;
    }

    return <span>{value}</span>;
  }, [matches, value, field]);
}

function Company({ company, matches }) {
  const name = useMatch(matches, 'name', company.name)
  const description = useMatch(matches, 'description', company.details?.description)
  const products = useMatch(matches, 'products_manufactured', company.details?.products_manufactured)

  return (
    <div key={company.detail_url} className="p-1 border rounded w-fit">
      <a
        href={company.detail_url}
        target="_blank"
        className="text-lg underline text-blue-600"
      >
        {name}
      </a>
      <div>
        <div className="font-bold">Description</div>
        {description}
      </div>
      <div>
        <div className="font-bold">Products Manufactured</div>
        {products}
      </div>
    </div>
  );
}

export default App;
