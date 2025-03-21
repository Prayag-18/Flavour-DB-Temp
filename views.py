# -*- coding: utf-8 -*-
# @Author: neelansh
# @Date:   2017-06-05 17:37:57
# @Last Modified by:   neelansh
# @Last Modified time: 2017-06-17 00:36:02
from django.shortcuts import render
from django.http import HttpResponse, JsonResponse, HttpResponseNotFound, Http404
from django.views.decorators.http import require_http_methods
from .forms import *
from .models import *
from django.core import serializers
import json
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Q
from datetime import datetime
from pybel import * # ---- CHANGED ----
# import pybel
import collections
from django.template.loader import render_to_string
import time 


@csrf_exempt
@require_http_methods(['GET'])
def home(request):
	today = datetime.now();
	try:
		moleculeoftheday = FDB_moleculeoftheday.objects.get(date = datetime(2016, today.month, today.day));
	except FDB_moleculeoftheday.DoesNotExist:
		#raise Http404("does not exist")
		#return HttpResponseNotFound('<h1>Not found</h1>')
		moleculeoftheday = FDB_moleculeoftheday.objects.get(date = datetime(2016, 1, 1));
	context = {'mol': moleculeoftheday.molecule}
	return render(request, 'common/home.html', context);	


@csrf_exempt
@require_http_methods(['GET'])
def index(request):
	today = datetime.now();
	try:
		moleculeoftheday = FDB_moleculeoftheday.objects.get(date = datetime(2016, today.month, today.day));
	except FDB_moleculeoftheday.DoesNotExist:
		#raise Http404("does not exist")
                #return HttpResponseNotFound('<h1>Not found</h1>')
                moleculeoftheday = FDB_moleculeoftheday.objects.get(date = datetime(2016, 1, 1));

	context = { 'f_ingredients' : search_ingredients(), 'mol': moleculeoftheday.molecule}
	return render(request, 'common/search.html', context);

# @csrf_exempt
# @require_http_methods(['GET'])
# def entities_name_autocomplete(request):


@csrf_exempt
@require_http_methods(['GET'])
def entities_json(request):
	if(not request.GET.get('id') ):
		raise Http404("does not exist")
		return HttpResponseNotFound('<h1>Not found</h1>')

	try:
		results = FDB_entities.objects.get(pk = request.GET.get('id'));
	except FDB_entities.DoesNotExist:
		raise Http404("does not exist")
		return HttpResponseNotFound('<h1>Not found</h1>')

	res_dict = results.__dict__.copy()
	del res_dict['_state']
	res_dict['molecules'] = []

	for mol in results.molecules.all():
		temp = mol.__dict__
		del temp['_state']
		res_dict['molecules'].append(temp)
	return JsonResponse(res_dict, safe=False);

@csrf_exempt
@require_http_methods(['GET'])
def entities(request):
	if(not request.GET.get('category') and not request.GET.get('entity') and not request.GET.get('natural_source')):
		raise Http404("does not exist");
		return HttpResponseNotFound('<h1>Not found</h1>');
	q = Q();
	if(request.GET.get('category')):
		q = q & Q(category_readable__icontains = request.GET.get('category'))
	if(request.GET.get('entity')):
		q = q & Q(entity_alias_readable__icontains = request.GET.get('entity')) | Q(entity_alias_synonyms__icontains = request.GET.get('entity'));
	if(request.GET.get('natural_source')):
		q = q & Q(natural_source_name__icontains = request.GET.get('natural_source'))
	try:
		results = FDB_entities.objects.filter(q);
	except FDB_entities.DoesNotExist:
		raise Http404("does not exist")
		return HttpResponseNotFound('<h1>Not found</h1>')
	
	results = list(results.values());
	if(request.GET.get('entity')):
		for val in results:
			lst = [val["entity_alias_readable"]]+val["entity_alias_synonyms"].split(', ')
			# print(lst)
			val["matched_term"] = list(set([x for x in lst if request.GET.get('entity').lower() in x.lower()]))

	entity_json = json.dumps(results);
	return JsonResponse(entity_json, safe=False);


@csrf_exempt
@require_http_methods(['GET'])
def entity_details(request):
	try:
		entity = FDB_entities.objects.get(entity_id = request.GET.get('id', 'does not exist'));
	except FDB_entities.DoesNotExist:
		raise Http404("does not exist")
		return HttpResponseNotFound('<h1>Not found</h1>')

	context = {'entity': entity, 'natural_source_template': 'natural_sources/'+str(entity.entity_id)+'.html', 'show_pair_it': True};
	return render(request, 'entities/entity_details.html', context);


@csrf_exempt
@require_http_methods(['GET'])
def molecules_details(request):
	if(not request.GET.get('id')):
		raise Http404("does not exist")
		return HttpResponseNotFound('<h1>Not found</h1>')
	try:
		q_molecules = FDB_molecules.objects.get(pubchem_id = request.GET.get('id'));
		fn_molecules={'name':""}
		print("q_molecules")
		print(q_molecules)
		print(q_molecules.fema_number)
		temp = ""
		if str(q_molecules.fema_number)!="":
			try:
				fn_molecules = FDB_fn_properties.objects.filter(fema_no__contains=str(q_molecules.fema_number))
				print("####################################")
				print(fn_molecules)
				fn_molecules = fn_molecules.get();
				print(fn_molecules.name)
				print(fn_molecules.fema_no)
				temp = str(fn_molecules.food_category_usual_max)
				temp = temp.replace("[","")
				temp = temp.replace("]","")
				temp = temp.split("',")
				for i in range(len(temp)):
					temp[i]=temp[i].replace("'","")
				print(temp)
			except FDB_fn_properties.DoesNotExist:
				fn_molecules={'name':""}
				print("HERE?")
		elif str(q_molecules.cas_id)!="":
			try:
				fn_molecules = FDB_fn_properties.objects.filter(cas_no__contains=str(q_molecules.cas_id))
				print("####################################")
				print(fn_molecules)
				fn_molecules = fn_molecules.get();
				print(fn_molecules.name)
				print(fn_molecules.cas_no)
				temp = str(fn_molecules.food_category_usual_max)
				temp = temp.replace("[","")
				temp = temp.replace("]","")
				temp = temp.split("',")
				for i in range(len(temp)):
					temp[i]=temp[i].replace("'","")
				print(temp)
			except FDB_fn_properties.DoesNotExist:
				fn_molecules={'name':""}
				print("HERE?")
		print("-----------------------------------------")
		print(fn_molecules)
	except FDB_molecules.DoesNotExist:
		raise Http404("does not exist")
		return HttpResponseNotFound('<h1>Not found</h1>')
	return HttpResponse(render_to_string('molecules/molecule_details.html', {'mol': q_molecules, 'fn_mol': fn_molecules, 'f_u_m': temp}))



@require_http_methods(['GET'])
def molecules_autocomplete(request):
	if(not request.GET.get('common_name') and not request.GET.get('functional_group') and not request.GET.get('fema_flavor_profile') and not request.GET.get('flavor_profile')):
		raise Http404("does not exist")
		return HttpResponseNotFound('<h1>Not found</h1>')

	q=Q();	

	if(request.GET.get('common_name')):
		q = q & Q(common_name__icontains = request.GET.get('common_name'));

	if(request.GET.get('functional_group')):
		q = q & Q(functional_groups__icontains = request.GET.get('functional_group'));

	if(request.GET.get('fema_flavor_profile')):
		q = q & Q(fema_flavor_profile__icontains = request.GET.get('fema_flavor_profile'));

	if(request.GET.get('flavor_profile')):
		q = q & Q(flavor_profile__icontains = request.GET.get('flavor_profile'));

	try:
		results = FDB_molecules.objects.filter(q);
	except FDB_molecules.DoesNotExist:
		raise Http404("does not exist")
		return HttpResponseNotFound('<h1>Not found</h1>')

	if(request.GET.get('common_name')):
		results = list(results.values_list('common_name', flat=True))
		# results = [str(x) for x in temp]

	if(request.GET.get('functional_group')):
		fp_results = []
		results_set = set(list(results.values_list('functional_groups', flat=True)))
		temp_set = set()
		for mol in results_set:
			functional_groups = str(mol).lower().split('@')
			temp_set = temp_set.union(set(functional_groups))
		for fp in temp_set:
			if(request.GET.get('functional_group').lower() in fp):
				fp_results.append(fp.strip())
		results = list(set(fp_results))

	if(request.GET.get('fema_flavor_profile')):
		fp_results = []
		results_set = set(list(results.values_list('fema_flavor_profile', flat=True)))
		temp_set = set()
		for mol in results_set:
			fema_flavor_profile = str(mol).lower().replace(', ', '@').split('@')
			temp_set = temp_set.union(set(fema_flavor_profile))
		for fp in temp_set:
			if(request.GET.get('fema_flavor_profile').lower() in fp):
				fp_results.append(fp.strip())
		results = list(set(fp_results))
		

	if(request.GET.get('flavor_profile')):
		fp_results = []
		results_set = set(list(results.values_list('flavor_profile', flat=True)))
		temp_set = set()
		for mol in results_set:
			flavor_profile = str(mol).lower().split('@')
			temp_set = temp_set.union(set(flavor_profile))
		for fp in temp_set:
			if(request.GET.get('flavor_profile').lower() in fp):
				fp_results.append(fp.strip())
		results = list(set(fp_results))


	res_json = json.dumps(results);
	return JsonResponse(res_json, safe=False);	


@require_http_methods(['GET'])
def advance_molecular_search(request):
	return render(request, 'common/advance_search.html');


def advance_search(request, q):
	if(request.GET.get('pubchem_id')):
		q = q & Q(pubchem_id = request.GET.get('pubchem_id'));
		return q;

	if(request.GET.get('rotatable_bonds')):
		if(':' in request.GET.get('rotatable_bonds')):
			q = q & Q(num_rotatablebonds__range = [int(request.GET.get('rotatable_bonds').split(':')[0]), int(request.GET.get('rotatable_bonds').split(':')[1])]);
		elif(request.GET.get('rotatable_bonds').isnumeric()):
			q = q & Q(num_rotatablebonds = int(request.GET.get('rotatable_bonds')))
		else:
			if not request.GET._mutable:
			   request.GET._mutable = True
			request.GET['rotatable_bonds'] = 'All'
			request.GET._mutable = False

	if(request.GET.get('topological_polar_sa')):
		if(':' in request.GET.get('topological_polar_sa')):
			q = q & Q(topological_polor_surfacearea__range = [float(request.GET.get('topological_polar_sa').split(':')[0]), float(request.GET.get('topological_polar_sa').split(':')[1])]);
		else:
			if not request.GET._mutable:
			   request.GET._mutable = True
			request.GET['topological_polar_sa'] = 'All'
			request.GET._mutable = False


	if(request.GET.get('monoisotopic_mass')):
		if(':' in request.GET.get('monoisotopic_mass')):
			q = q & Q(monoisotopic_mass__range = [float(request.GET.get('monoisotopic_mass').split(':')[0]), float(request.GET.get('monoisotopic_mass').split(':')[1])]);
		else:
			if not request.GET._mutable:
			   request.GET._mutable = True
			request.GET['monoisotopic_mass'] = 'All'
			request.GET._mutable = False


	if(request.GET.get('heavy_atom_count')):
		if(':' in request.GET.get('heavy_atom_count')):
			q = q & Q(heavy_atom_count__range = [int(request.GET.get('heavy_atom_count').split(':')[0]), int(request.GET.get('heavy_atom_count').split(':')[1])]);
		elif(request.GET.get('heavy_atom_count').isnumeric()):
			q = q & Q(heavy_atom_count = int(request.GET.get('heavy_atom_count')))
		else:
			if not request.GET._mutable:
			   request.GET._mutable = True
			request.GET['heavy_atom_count'] = 'All'
			request.GET._mutable = False


	if(request.GET.get('num_rings')):
		if(':' in request.GET.get('num_rings')):
			q = q & Q(more_properties__num_rings__range = [int(request.GET.get('num_rings').split(':')[0]), int(request.GET.get('num_rings').split(':')[1])]);
		elif(request.GET.get('num_rings').isnumeric()):
			q = q & Q(more_properties__num_rings = int(request.GET.get('num_rings')))
		else:
			if not request.GET._mutable:
			   request.GET._mutable = True
			request.GET['num_rings'] = 'All'
			request.GET._mutable = False

	if(request.GET.get('number_of_atoms')):
		if(':' in request.GET.get('number_of_atoms')):
			q = q & Q(more_properties__number_of_atoms__range = [int(request.GET.get('number_of_atoms').split(':')[0]), int(request.GET.get('number_of_atoms').split(':')[1])]);
		elif(request.GET.get('number_of_atoms').isnumeric()):
			q = q & Q(more_properties__number_of_atoms = int(request.GET.get('number_of_atoms')))
		else:
			if not request.GET._mutable:
			   request.GET._mutable = True
			request.GET['number_of_atoms'] = 'All'
			request.GET._mutable = False


	if(request.GET.get('number_of_aromatic_rings')):
		if(':' in request.GET.get('number_of_aromatic_rings')):
			q = q & Q(more_properties__number_of_aromatic_rings__range = [int(request.GET.get('number_of_aromatic_rings').split(':')[0]), int(request.GET.get('number_of_aromatic_rings').split(':')[1])]);
		elif(request.GET.get('number_of_aromatic_rings').isnumeric()):
			q = q & Q(more_properties__number_of_aromatic_rings = int(request.GET.get('number_of_aromatic_rings')))
		else:
			if not request.GET._mutable:
			   request.GET._mutable = True
			request.GET['number_of_aromatic_rings'] = 'All'
			request.GET._mutable = False


	if(request.GET.get('number_of_aromatic_bonds')):
		if(':' in request.GET.get('number_of_aromatic_bonds')):
			q = q & Q(more_properties__number_of_aromatic_bonds__range = [int(request.GET.get('number_of_aromatic_bonds').split(':')[0]), int(request.GET.get('number_of_aromatic_bonds').split(':')[1])]);
		elif(request.GET.get('number_of_aromatic_bonds').isnumeric()):
			q = q & Q(more_properties__number_of_aromatic_bonds = int(request.GET.get('number_of_aromatic_bonds')))
		else:
			if not request.GET._mutable:
			   request.GET._mutable = True
			request.GET['number_of_aromatic_bonds'] = 'All'
			request.GET._mutable = False

	if(request.GET.get('energy')):
		if(':' in request.GET.get('energy')):
			q = q & Q(more_properties__energy__range = [float(request.GET.get('energy').split(':')[0]), float(request.GET.get('energy').split(':')[1])]);
		else:
			if not request.GET._mutable:
			   request.GET._mutable = True
			request.GET['energy'] = 'All'
			request.GET._mutable = False

	if(request.GET.get('alogp')):
		if(':' in request.GET.get('alogp')):
			q = q & Q(more_properties__alogp__range = [float(request.GET.get('alogp').split(':')[0]), float(request.GET.get('alogp').split(':')[1])]);
		else:
			if not request.GET._mutable:
			   request.GET._mutable = True
			request.GET['alogp'] = 'All'
			request.GET._mutable = False

	if(request.GET.get('surface_area')):
		if(':' in request.GET.get('surface_area')):
			q = q & Q(more_properties__surface_area__range = [float(request.GET.get('surface_area').split(':')[0]), float(request.GET.get('surface_area').split(':')[1])]);
		else:
			if not request.GET._mutable:
			   request.GET._mutable = True
			request.GET['surface_area'] = 'All'
			request.GET._mutable = False


	return q;


@csrf_exempt
@require_http_methods(['GET'])
def molecules_json(request):
	if(not request.GET.get('id') ):
		raise Http404("does not exist")
		return HttpResponseNotFound('<h1>Not found</h1>')

	try:
		results = FDB_molecules.objects.get(pk = request.GET.get('id'));
	except FDB_molecules.DoesNotExist:
		raise Http404("does not exist")
		return HttpResponseNotFound('<h1>Not found</h1>')

	res_dict = results.__dict__.copy()
	del res_dict['_state']
	return JsonResponse(res_dict, safe=False);


@csrf_exempt
@require_http_methods(['GET'])
def molecules(request):
	# if(not request.GET.get('common_name') and not request.GET.get('molecular_weight_from') and not request.GET.get('molecular_weight_to') and not request.GET.get('h_bond_donors') and not request.GET.get('h_bond_acceptors') and not request.GET.get('smile') and not request.GET.get('functional_group')):
	# 	raise Http404("does not exist")
	# 	return HttpResponseNotFound('<h1>Not found</h1>')

	# start_time = time.time();
	q=Q();

	if(request.GET.get('type')):
		if(request.GET.get('type').lower() == 'natural'):
			q = q & Q(natural = 1);
		elif(request.GET.get('type').lower() == 'synthetic'):
			q = q & Q(synthetic = 1);
		elif(request.GET.get('type').lower() == 'unknown'):
			q = q & Q(natural = 0) & Q(synthetic = 0);

	if(request.GET.get('common_name')):
		q = q & Q(common_name__icontains = request.GET.get('common_name'));

	if(request.GET.get('molecular_weight_from')):
		q = q & Q(molecular_weight__range = [int(request.GET.get('molecular_weight_from')), 1000]);
		if(not request.GET.get('molecular_weight_to')):
			if not request.GET._mutable:
			   request.GET._mutable = True
			request.GET['molecular_weight_to'] = 1000
			request.GET._mutable = False

	if(request.GET.get('molecular_weight_to')):
		q = q & Q(molecular_weight__range = [0, int(request.GET.get('molecular_weight_to'))]);
		if(not request.GET.get('molecular_weight_from')):
			if not request.GET._mutable:
			   request.GET._mutable = True
			request.GET['molecular_weight_from'] = 0
			request.GET._mutable = False

	if(request.GET.get('h_bond_donors')):
		if(':' in request.GET.get('h_bond_donors')):
			q = q & Q(hbd_count__range = [int(request.GET.get('h_bond_donors').split(':')[0]), int(request.GET.get('h_bond_donors').split(':')[1])]);
		elif(request.GET.get('h_bond_donors').isnumeric()):
			q = q & Q(hbd_count = int(request.GET.get('h_bond_donors')))
		else:
			if not request.GET._mutable:
			   request.GET._mutable = True
			request.GET['h_bond_donors'] = 'All'
			request.GET._mutable = False

	if(request.GET.get('h_bond_acceptors')):
		if(':' in request.GET.get('h_bond_acceptors')):
			q = q & Q(hba_count__range = [int(request.GET.get('h_bond_acceptors').split(':')[0]), int(request.GET.get('h_bond_acceptors').split(':')[1])]);
		elif(request.GET.get('h_bond_acceptors').isnumeric()):
			q = q & Q(hba_count = int(request.GET.get('h_bond_acceptors')))
		else:
			if not request.GET._mutable:
			   request.GET._mutable = True
			request.GET['h_bond_acceptors'] = 'All'
			request.GET._mutable = False

	if(request.GET.get('functional_group')):
		q = q & Q(functional_groups__icontains = request.GET.get('functional_group').lower());

	if(request.GET.get('fema_flavor')):
		q = q & Q(fema_flavor_profile__icontains = request.GET.get('fema_flavor').lower());

	if(request.GET.get('flavor_profile')):
		q = q & Q(flavor_profile__icontains = request.GET.get('flavor_profile').lower());


	if(request.GET.get('advance_search') == 'true'):
		q = advance_search(request, q);


	
	if(request.GET.get('smile')):
		try:
			results = FDB_molecules.objects.filter(q);
		except FDB_molecules.DoesNotExist:
			raise Http404("does not exist")
			return HttpResponseNotFound('<h1>Not found</h1>')
	else:
		try:
			i = int(request.GET.get('page'));
			results = FDB_molecules.objects.filter(q).order_by('pubchem_id');
			if(results.count() < (i-1)*50):
				raise Http404("does not exist")
				return HttpResponseNotFound('<h1>Page Not found</h1>')
			results_length = results.count();
			results = results[(i-1)*50:i*50];
			# if not request.GET._mutable:
			#    request.GET._mutable = True
			# request.GET['page'] = i+1;
			# request.GET._mutable = False
		except FDB_molecules.DoesNotExist:
			raise Http404("does not exist")
			return HttpResponseNotFound('<h1>Not found</h1>')

	if(request.GET.get('functional_group')):
		fp_results = []
		for mol in results:
			functional_groups = mol.functional_groups.split('@')
			if(request.GET.get('functional_group').lower() in [x.lower() for x in functional_groups]):
				fp_results.append(mol)
		results = fp_results

	if(request.GET.get('fema_flavor')):
		ff_results = []
		for mol in results:
			fema_flavors = mol.fema_flavor_profile.replace('@', ', ').lower().split(', ');
			if(request.GET.get('fema_flavor').lower() in [x.lower() for x in fema_flavors]):
				ff_results.append(mol)
		results = ff_results

	if(request.GET.get('flavor_profile')):
		f_results = []
		for mol in results:
			flavor_profile = mol.flavor_profile.replace('@', ', ').lower().split(', ');
			if(request.GET.get('flavor_profile').lower() in [x.lower() for x in flavor_profile]):
				f_results.append(mol)
		results = f_results

	if(request.GET.get('smile')):
		final_res = {};

		q_fps = readstring("smi", str(request.GET.get('smile'))).calcfp();

		for res in results:
			try:
			 	fps = readstring("smi", str(res.smile)).calcfp();
			 	tanimoto = fps | q_fps
			 	if(tanimoto > 0.3):
			 		# final_res.append(res);
			 		final_res['%.3f'%tanimoto] = res;
			except Exception as e:
				print(e)

		final_res = collections.OrderedDict(sorted(final_res.items(), reverse=True));
	

		return render(request, 'molecules/molecules_similarity.html', {'molecules': final_res});

	# print("--- %s seconds ---" % (time.time() - start_time))
	# res_dict = [];
	# for mol in results:
	# 	res_dict.append({'pubchem_id': mol.pubchem_id, 'common_name': str(mol.common_name), 'flavor_profile': str(mol.flavor_profile).replace('@', ', ')})
	path_para = request.get_full_path().split('?')[1].split('&');
	for para in path_para:
		if("page" in para):
			path_para.remove(para);
	next_page_path = '&'.join(path_para)+'&page='+str(i+1);

	context = {'molecules': results, 'path': next_page_path, 'results_length': results_length, 'page_no': i, 'show_next': results_length > i*50};
	return render(request, 'molecules/molecules.html', context);
	# return JsonResponse(serializers.serialize('json', results), safe=True)


@csrf_exempt
@require_http_methods(['GET'])
def food_pairing(request):
	if(not request.GET.get('id')):
		raise Http404("does not exist")
		return HttpResponseNotFound('<h1>Not found</h1>')
	try:
		entity = FDB_entities.objects.get(pk = request.GET.get('id'))
	except FDB_entities.DoesNotExist:
		raise Http404("does not exist")
		return HttpResponseNotFound('<h1>Not found</h1>')
	return render(request, 'food_pairing/food_pairing.html', {'entity': entity, 'natural_source_template': 'natural_sources/'+str(entity.entity_id)+'.html'});


@require_http_methods(['GET'])
def food_pairing_analysis(request):
	if(not request.GET.get('id')):
		raise Http404("does not exist")
		return HttpResponseNotFound('<h1>Not found</h1>')
	try:
		q_entity = FDB_entities.objects.get(pk = request.GET.get('id'));
		set_q_entity = set(q_entity.molecules.all().values_list('pubchem_id'));
		entities_set = {};
		for entity in FDB_entities.objects.all():
			entities_set[entity.entity_id] = {"entity_details":{"id": entity.entity_id, "name": entity.entity_alias_readable, "category": entity.category_readable, "wiki": entity.entity_alias_url} , "common_molecules": set(entity.molecules.all().values_list('pubchem_id'))}
		no_common_molecules = []
		for k,v in entities_set.iteritems():
			if(not set_q_entity.intersection(v['common_molecules'])):
				no_common_molecules.append(k)
			else:
				entities_set[k]["common_molecules"] = list(set_q_entity.intersection(v['common_molecules']));
		for k in no_common_molecules:
			entities_set.pop(k, None);
		entities_set.pop(int(request.GET.get('id')), None);
	except:
		return HttpResponse(status=500)
	return JsonResponse(json.dumps(entities_set), safe=False);




@csrf_exempt
@require_http_methods(['POST'])
def food_pairing_molecules(request):
	if(not request.POST.get('mol_id')):
		raise Http404("does not exist")
		return HttpResponseNotFound('<h1>Not found</h1>')
	molecules = []
	try:
		for mol in json.loads(request.POST.get('mol_id')):
			molecules.append(FDB_molecules.objects.get(pk = mol[0]));
		entity1 = FDB_entities.objects.get(pk=request.POST.get('entity_id1'))
		entity2 = FDB_entities.objects.get(pk=request.POST.get('entity_id2'))
	except:
		return HttpResponse(status=500)
	return HttpResponse(render_to_string('food_pairing/food_pairing_molecules.html', {'molecules': molecules, 'entity1': entity1, 'entity2': entity2}))


# @csrf_exempt
# @require_http_methods(['GET'])
# def plant_details(request):
# 	q_plants = flavorDB_ingredients_plants.objects.get(pk = request.GET.get('id'));
# 	context = {'plant': q_plants }
# 	return render(request, 'plants/plants.html', context);

@csrf_exempt
@require_http_methods(['GET'])
def faq(request):
	return render(request, 'common/faq.html');

@csrf_exempt
@require_http_methods(['GET'])
def contact(request):
	return render(request, 'common/contact.html');

@csrf_exempt
@require_http_methods(['GET'])
def how_to_use(request):
	return render(request, 'common/how_to_use.html');



@csrf_exempt
@require_http_methods(['GET'])
def receptors(request):
	receptors = FDB_receptors.objects.all()

	return render(request, 'common/receptors.html', {'receptors': receptors});
